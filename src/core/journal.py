"""
Journal/WAL module - MEMBER 3

Nhiệm vụ:
- Write-Ahead Logging cho crash consistency
- Format: BEGIN/WRITE/COMMIT
- Recovery: rollback uncommitted transactions
- PHẢI dùng fsync() để đảm bảo ghi xuống disk

Tham khảo: src/interfaces.py

Yêu cầu bài tập:
- Crash consistency: nếu kill/crash khi backup, snapshot dang dở không được xuất hiện
- Store vẫn chạy bình thường ở lần chạy sau
- Journal/WAL là file append-only chứa BEGIN, các record cập nhật metadata, và COMMIT
- Khi khởi động lại, hệ thống đọc journal để xử lý giao dịch chưa commit
"""

import os
import time
import json
from typing import Dict, List, Set, Optional


def init_journal(store_path: str) -> None:
    """
    Khởi tạo journal/WAL file.
    Tạo: store_path/journal.wal
    
    Args:
        store_path: Đường dẫn đến backup store
    """
    journal_path = os.path.join(store_path, "journal.wal")
    
    # Tạo thư mục store nếu chưa có
    os.makedirs(store_path, exist_ok=True)
    
    # Tạo file journal nếu chưa có
    if not os.path.exists(journal_path):
        with open(journal_path, 'w', encoding='utf-8') as f:
            # File rỗng ban đầu
            pass


def journal_begin(store_path: str, operation: str) -> str:
    """
    Bắt đầu một transaction.
    Ghi: BEGIN <txn_id> <operation> <timestamp>
    
    Args:
        store_path: Đường dẫn đến backup store
        operation: Tên operation (ví dụ: "backup")
    
    Returns:
        Transaction ID (unique)
    """
    # Tạo unique transaction ID dựa trên timestamp milliseconds
    txn_id = f"txn_{int(time.time() * 1000)}"
    timestamp = int(time.time())
    
    journal_path = os.path.join(store_path, "journal.wal")
    
    # Ghi BEGIN vào journal với fsync
    with open(journal_path, 'a', encoding='utf-8') as f:
        f.write(f"BEGIN {txn_id} {operation} {timestamp}\n")
        f.flush()
        os.fsync(f.fileno())  # CRITICAL: Đảm bảo ghi xuống disk
    
    return txn_id


def journal_write(store_path: str, txn_id: str, record: dict) -> None:
    """
    Ghi một record vào journal.
    Ghi: WRITE <txn_id> <record_json>
    
    Args:
        store_path: Đường dẫn đến backup store
        txn_id: Transaction ID
        record: Dữ liệu record dạng dict
    """
    journal_path = os.path.join(store_path, "journal.wal")
    
    # Serialize record thành JSON (deterministic)
    record_json = json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    
    # Ghi WRITE vào journal với fsync
    with open(journal_path, 'a', encoding='utf-8') as f:
        f.write(f"WRITE {txn_id} {record_json}\n")
        f.flush()
        os.fsync(f.fileno())  # CRITICAL: Đảm bảo ghi xuống disk


def journal_commit(store_path: str, txn_id: str) -> None:
    """
    Commit một transaction.
    Ghi: COMMIT <txn_id> <timestamp>
    
    Args:
        store_path: Đường dẫn đến backup store
        txn_id: Transaction ID
    """
    journal_path = os.path.join(store_path, "journal.wal")
    timestamp = int(time.time())
    
    # Ghi COMMIT vào journal với fsync
    with open(journal_path, 'a', encoding='utf-8') as f:
        f.write(f"COMMIT {txn_id} {timestamp}\n")
        f.flush()
        os.fsync(f.fileno())  # CRITICAL: Đảm bảo ghi xuống disk


def journal_recover(store_path: str) -> None:
    """
    Khôi phục sau crash bằng cách xử lý journal.
    
    - Đọc journal.wal
    - Với mỗi uncommitted transaction: rollback (xóa snapshot chưa hoàn thành)
    - Dọn dẹp journal
    
    Args:
        store_path: Đường dẫn đến backup store
    """
    journal_path = os.path.join(store_path, "journal.wal")
    
    # Nếu journal không tồn tại, không cần recover
    if not os.path.exists(journal_path):
        return
    
    # Đọc toàn bộ journal
    with open(journal_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if not lines:
        return
    
    # Parse journal để tìm uncommitted transactions
    transactions: Dict[str, Dict] = {}  # txn_id -> {operation, records, committed}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split(maxsplit=2)
        if len(parts) < 2:
            continue
        
        command = parts[0]
        
        if command == "BEGIN":
            # BEGIN <txn_id> <operation> <timestamp>
            if len(parts) >= 3:
                txn_id = parts[1]
                operation_and_timestamp = parts[2].split(maxsplit=1)
                operation = operation_and_timestamp[0] if operation_and_timestamp else "unknown"
                
                transactions[txn_id] = {
                    'operation': operation,
                    'records': [],
                    'committed': False
                }
        
        elif command == "WRITE":
            # WRITE <txn_id> <record_json>
            if len(parts) >= 3:
                txn_id = parts[1]
                record_json = parts[2]
                
                if txn_id in transactions:
                    try:
                        record = json.loads(record_json)
                        transactions[txn_id]['records'].append(record)
                    except json.JSONDecodeError:
                        pass
        
        elif command == "COMMIT":
            # COMMIT <txn_id> <timestamp>
            if len(parts) >= 2:
                txn_id = parts[1]
                
                if txn_id in transactions:
                    transactions[txn_id]['committed'] = True
    
    # Tìm uncommitted transactions và rollback
    uncommitted_txns = [
        txn_id for txn_id, txn_data in transactions.items()
        if not txn_data['committed']
    ]
    
    if uncommitted_txns:
        # Rollback: xóa snapshots từ uncommitted transactions
        _rollback_transactions(store_path, transactions, uncommitted_txns)
    
    # Dọn dẹp journal: tạo journal mới (hoặc archive journal cũ)
    # Chiến lược: xóa journal cũ và tạo mới
    # (Trong production, nên archive journal cũ để audit)
    with open(journal_path, 'w', encoding='utf-8') as f:
        # Clear journal
        pass


def _rollback_transactions(store_path: str, transactions: Dict, uncommitted_txns: List[str]) -> None:
    """
    Rollback uncommitted transactions bằng cách xóa snapshots chưa hoàn thành.
    
    Args:
        store_path: Đường dẫn đến backup store
        transactions: Dict chứa thông tin transactions
        uncommitted_txns: List các transaction IDs chưa commit
    """
    snapshots_dir = os.path.join(store_path, "snapshots")
    
    if not os.path.exists(snapshots_dir):
        return
    
    # Collect snapshot IDs từ uncommitted transactions
    snapshot_ids_to_delete: Set[str] = set()
    
    for txn_id in uncommitted_txns:
        txn_data = transactions.get(txn_id, {})
        records = txn_data.get('records', [])
        
        # Tìm snapshot_id trong records
        for record in records:
            if isinstance(record, dict) and 'snapshot_id' in record:
                snapshot_ids_to_delete.add(record['snapshot_id'])
    
    # Xóa snapshots chưa hoàn thành
    for snapshot_id in snapshot_ids_to_delete:
        snapshot_path = os.path.join(snapshots_dir, f"{snapshot_id}.json")
        
        if os.path.exists(snapshot_path):
            try:
                os.remove(snapshot_path)
                print(f"[Journal Recovery] Rolled back uncommitted snapshot: {snapshot_id}")
            except OSError as e:
                print(f"[Journal Recovery] Warning: Failed to delete {snapshot_id}: {e}")


# ============= TESTING FUNCTIONS =============

def _test_journal():
    """Test function để verify journal hoạt động đúng."""
    import tempfile
    import shutil
    
    print("=== Journal/WAL Test ===\n")
    
    # Tạo temporary store
    test_store = tempfile.mkdtemp(prefix="test_journal_")
    
    try:
        # Test 1: Basic flow (BEGIN -> WRITE -> COMMIT)
        print("Test 1: Basic flow (BEGIN -> WRITE -> COMMIT)")
        init_journal(test_store)
        
        txn_id = journal_begin(test_store, "backup")
        print(f"  Started transaction: {txn_id}")
        
        journal_write(test_store, txn_id, {"snapshot_id": "snapshot_123", "label": "test"})
        print(f"  Wrote record to transaction")
        
        journal_commit(test_store, txn_id)
        print(f"  Committed transaction")
        
        # Verify journal file
        journal_path = os.path.join(test_store, "journal.wal")
        with open(journal_path, 'r') as f:
            content = f.read()
            assert "BEGIN" in content
            assert "WRITE" in content
            assert "COMMIT" in content
        print("  ✅ Test 1 PASSED\n")
        
        # Test 2: Crash recovery (BEGIN -> WRITE, no COMMIT)
        print("Test 2: Crash recovery (uncommitted transaction)")
        
        # Tạo snapshot file giả
        os.makedirs(os.path.join(test_store, "snapshots"), exist_ok=True)
        snapshot_path = os.path.join(test_store, "snapshots", "snapshot_999.json")
        with open(snapshot_path, 'w') as f:
            json.dump({"id": "snapshot_999"}, f)
        
        # Tạo uncommitted transaction
        txn_id2 = journal_begin(test_store, "backup")
        journal_write(test_store, txn_id2, {"snapshot_id": "snapshot_999"})
        # NO COMMIT - simulate crash
        
        print(f"  Created uncommitted transaction: {txn_id2}")
        print(f"  Snapshot file exists: {os.path.exists(snapshot_path)}")
        
        # Recover
        journal_recover(test_store)
        print(f"  Ran journal_recover()")
        
        # Verify snapshot was deleted
        assert not os.path.exists(snapshot_path), "Snapshot should be deleted after rollback"
        print(f"  Snapshot file deleted: {not os.path.exists(snapshot_path)}")
        print("  ✅ Test 2 PASSED\n")
        
        # Test 3: fsync verification (just check it doesn't crash)
        print("Test 3: fsync verification")
        init_journal(test_store)
        txn_id3 = journal_begin(test_store, "test_fsync")
        journal_commit(test_store, txn_id3)
        print("  ✅ Test 3 PASSED (fsync works)\n")
        
        print("=== All Journal Tests PASSED ===")
        
    finally:
        # Cleanup
        shutil.rmtree(test_store, ignore_errors=True)


if __name__ == "__main__":
    # Chạy tests khi file được chạy trực tiếp
    _test_journal()
