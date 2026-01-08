"""
CLI command implementations - MEMBER 3

Nhiệm vụ:
- Implement 6 commands: init, backup, list-snapshots, verify, restore, audit-verify
- Mỗi command phải:
  1. Check permission (Member 4)
  2. Use journal (Member 3)
  3. Log audit (Member 4)
- Integrate tất cả modules (Member 1, 2, 4)

Tham khảo: src/interfaces.py, TASK_ASSIGNMENT.md (Integration points)
"""

import os
import sys
from typing import List
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============= HELPER FUNCTIONS =============

def scan_directory(path: str) -> List[str]:
    """
    Quét thư mục đệ quy và trả về danh sách đường dẫn file.
    
    Args:
        path: Đường dẫn thư mục cần quét
    
    Returns:
        Danh sách đường dẫn file tuyệt đối (không bao gồm thư mục), đã sắp xếp
    
    Raises:
        FileNotFoundError: Nếu path không tồn tại
        NotADirectoryError: Nếu path không phải là thư mục
    
    Example:
        >>> files = scan_directory("dataset/")
        >>> print(files)
        ['/path/to/dataset/file1.txt', '/path/to/dataset/subdir/file2.txt']
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Path is not a directory: {path}")
    
    files = []
    
    # Walk through directory tree
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            # Convert to absolute path
            abs_path = os.path.abspath(file_path)
            files.append(abs_path)
    
    # Sort files for deterministic order
    return sorted(files)


# ============= COMMAND IMPLEMENTATIONS =============

def cmd_init(store_path: str) -> None:
    """
    Initialize backup store.
    
    Args:
        store_path: Path to backup store
    """
    from src.security.policy import check_permission
    from src.security.audit import log_audit
    from src.core.storage import init_storage
    from src.core.journal import init_journal
    
    # 1. Check permission
    if not check_permission("init"):
        log_audit("init", [store_path], "DENY")
        raise PermissionError("Permission denied for 'init' command")
    
    try:
        # 2. Initialize storage (creates chunks/ directory)
        init_storage(store_path)
        
        # 3. Initialize journal
        init_journal(store_path)
        
        # 4. Create other required directories
        os.makedirs(os.path.join(store_path, "snapshots"), exist_ok=True)
        os.makedirs(os.path.join(store_path, "manifests"), exist_ok=True)
        
        # 5. Log audit
        log_audit("init", [store_path], "OK", os.path.join(store_path, "audit.log"))
        
        print(f"✅ Backup store initialized at {store_path}")
        
    except Exception as e:
        log_audit("init", [store_path], "FAIL")
        raise


def cmd_backup(store_path: str, source_path: str, label: str) -> None:
    """
    Create a backup snapshot.
    
    Args:
        store_path: Path to backup store
        source_path: Path to source directory to backup
        label: Snapshot label
    """
    from src.security.policy import check_permission
    from src.security.audit import log_audit
    from src.core.journal import journal_begin, journal_write, journal_commit, journal_recover
    from src.core.chunker import chunk_file
    from src.core.storage import store_chunk
    from src.core.manifest import create_manifest, serialize_manifest, hash_manifest
    from src.core.snapshot import create_snapshot, get_latest_snapshot
    from src.interfaces import FileEntry
    import json
    
    # 0. Run journal recovery first (crash consistency)
    journal_recover(store_path)
    
    # 1. Check permission
    if not check_permission("backup"):
        log_audit("backup", [source_path, "--label", label], "DENY", 
                 os.path.join(store_path, "audit.log"))
        raise PermissionError("Permission denied for 'backup' command")
    
    try:
        # 2. Start journal transaction
        txn_id = journal_begin(store_path, "backup")
        
        # 3. Scan directory
        print(f"Scanning directory: {source_path}")
        files = scan_directory(source_path)
        print(f"Found {len(files)} files to backup")
        
        # 4. Chunk and store files
        file_entries = []
        total_chunks = 0
        
        for i, file_path in enumerate(files, 1):
            print(f"Processing file {i}/{len(files)}: {os.path.basename(file_path)}")
            
            # Chunk file
            chunks = chunk_file(file_path)
            chunk_hashes = []
            
            # Store each chunk
            for chunk in chunks:
                chunk_hash = store_chunk(store_path, chunk)
                chunk_hashes.append(chunk_hash)
                total_chunks += 1
            
            # Create file entry with relative path
            rel_path = os.path.relpath(file_path, source_path)
            file_entries.append(FileEntry(path=rel_path, chunks=chunk_hashes))
        
        print(f"Stored {total_chunks} chunks (with deduplication)")
        
        # 5. Create canonical manifest
        manifest = create_manifest(file_entries)
        
        # 6. Save manifest to manifests/ directory
        manifest_hash = hash_manifest(manifest)
        manifest_path = os.path.join(store_path, "manifests", f"{manifest_hash}.json")
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(serialize_manifest(manifest))
        
        # 7. Get prev_root for anti-rollback
        prev_snapshot = get_latest_snapshot(store_path)
        prev_root = prev_snapshot.merkle_root if prev_snapshot else ""
        
        # 8. Create snapshot
        snapshot_id = create_snapshot(store_path, manifest, label, prev_root)
        
        # 9. Journal write (record snapshot metadata)
        journal_write(store_path, txn_id, {"snapshot_id": snapshot_id, "label": label})
        
        # 10. Commit journal
        journal_commit(store_path, txn_id)
        
        # 11. Log audit
        log_audit("backup", [source_path, "--label", label], "OK",
                 os.path.join(store_path, "audit.log"))
        
        print(f"✅ Backup created: {snapshot_id}")
        
    except Exception as e:
        log_audit("backup", [source_path, "--label", label], "FAIL",
                 os.path.join(store_path, "audit.log"))
        raise


def cmd_list_snapshots(store_path: str) -> None:
    """
    List all snapshots.
    
    Args:
        store_path: Path to backup store
    """
    from src.security.policy import check_permission
    from src.security.audit import log_audit
    from src.core.snapshot import list_snapshots
    
    # 1. Check permission
    if not check_permission("list-snapshots"):
        log_audit("list-snapshots", [], "DENY",
                 os.path.join(store_path, "audit.log"))
        raise PermissionError("Permission denied for 'list-snapshots' command")
    
    try:
        # 2. List snapshots
        snapshots = list_snapshots(store_path)
        
        # 3. Print table
        if not snapshots:
            print("No snapshots found")
        else:
            print(f"\n{'ID':<30} {'Label':<30} {'Timestamp':<20} {'Merkle Root':<20}")
            print("-" * 105)
            for snap in snapshots:
                timestamp_str = datetime.fromtimestamp(snap.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                merkle_short = snap.merkle_root[:16] + "..."
                print(f"{snap.id:<30} {snap.label:<30} {timestamp_str:<20} {merkle_short:<20}")
            print(f"\nTotal: {len(snapshots)} snapshot(s)")
        
        # 4. Log audit
        log_audit("list-snapshots", [], "OK",
                 os.path.join(store_path, "audit.log"))
        
    except Exception as e:
        log_audit("list-snapshots", [], "FAIL",
                 os.path.join(store_path, "audit.log"))
        raise


def cmd_verify(store_path: str, snapshot_id: str) -> None:
    """
    Verify a snapshot's integrity.
    
    Args:
        store_path: Path to backup store
        snapshot_id: Snapshot ID to verify
    """
    from src.security.policy import check_permission
    from src.security.audit import log_audit
    from src.core.snapshot import load_snapshot, load_manifest, list_snapshots
    from src.core.merkle import verify_merkle_root
    from src.core.storage import chunk_exists, get_chunk
    
    # 1. Check permission
    if not check_permission("verify"):
        log_audit("verify", [snapshot_id], "DENY",
                 os.path.join(store_path, "audit.log"))
        raise PermissionError("Permission denied for 'verify' command")
    
    try:
        print(f"Verifying snapshot: {snapshot_id}")
        
        # 2. Load snapshot
        snapshot = load_snapshot(store_path, snapshot_id)
        
        # 3. Load manifest
        manifest = load_manifest(store_path, snapshot.manifest_hash)
        
        # 4. Verify Merkle root
        print("Checking Merkle root...")
        if not verify_merkle_root(manifest, snapshot.merkle_root):
            print(f"❌ VERIFY FAILED: Merkle root mismatch for {snapshot_id}")
            log_audit("verify", [snapshot_id], "FAIL",
                     os.path.join(store_path, "audit.log"))
            return
        
        # 5. Verify all chunks exist and have correct integrity
        print("Checking chunks integrity...")
        total_chunks = sum(len(file_entry["chunks"]) for file_entry in manifest["files"])
        checked_chunks = 0
        
        for file_entry in manifest["files"]:
            for chunk_hash in file_entry["chunks"]:
                # Check chunk exists
                if not chunk_exists(store_path, chunk_hash):
                    print(f"❌ VERIFY FAILED: Missing chunk {chunk_hash}")
                    log_audit("verify", [snapshot_id], "FAIL",
                             os.path.join(store_path, "audit.log"))
                    return
                
                # Verify chunk integrity (get_chunk does hash verification)
                try:
                    get_chunk(store_path, chunk_hash)
                    checked_chunks += 1
                except ValueError as e:
                    print(f"❌ VERIFY FAILED: Chunk integrity check failed for {chunk_hash}")
                    log_audit("verify", [snapshot_id], "FAIL",
                             os.path.join(store_path, "audit.log"))
                    return
        
        print(f"Verified {checked_chunks} chunks")
        
        # 6. Check anti-rollback (prev_root chain)
        print("Checking anti-rollback chain...")
        
        # Note: We do NOT check if merkle_root == prev_root because:
        # - If dataset doesn't change, merkle_root SHOULD be the same (valid!)
        # - Actual rollback attacks are detected by Merkle root verification (step 4)
        # - If attacker modifies merkle_root, it won't match the manifest
        
        # Check: prev_root should match previous snapshot's merkle_root
        snapshots = list_snapshots(store_path)
        
        # Find current snapshot index
        current_index = None
        for i, snap in enumerate(snapshots):
            if snap.id == snapshot_id:
                current_index = i
                break
        
        if current_index is not None and current_index > 0:
            # Verify prev_root matches previous snapshot's merkle_root
            prev_snapshot = snapshots[current_index - 1]
            if snapshot.prev_root != prev_snapshot.merkle_root:
                print(f"❌ VERIFY FAILED: Anti-rollback check failed (prev_root mismatch)")
                print(f"   Expected prev_root: {prev_snapshot.merkle_root}")
                print(f"   Actual prev_root: {snapshot.prev_root}")
                log_audit("verify", [snapshot_id], "FAIL",
                         os.path.join(store_path, "audit.log"))
                return
        
        # 7. Success
        print(f"✅ VERIFY OK: {snapshot_id}")
        log_audit("verify", [snapshot_id], "OK",
                 os.path.join(store_path, "audit.log"))
        
    except FileNotFoundError as e:
        print(f"❌ VERIFY FAILED: {e}")
        log_audit("verify", [snapshot_id], "FAIL",
                 os.path.join(store_path, "audit.log"))
        raise
    except Exception as e:
        log_audit("verify", [snapshot_id], "FAIL",
                 os.path.join(store_path, "audit.log"))
        raise


def cmd_restore(store_path: str, snapshot_id: str, target_path: str) -> None:
    """
    Restore a snapshot to target directory.
    
    Args:
        store_path: Path to backup store
        snapshot_id: Snapshot ID to restore
        target_path: Target directory for restore
    """
    from src.security.policy import check_permission
    from src.security.audit import log_audit
    from src.core.snapshot import load_snapshot, load_manifest
    from src.core.storage import get_chunk
    from src.core.merkle import verify_merkle_root
    
    # 1. Check permission
    if not check_permission("restore"):
        log_audit("restore", [snapshot_id, target_path], "DENY",
                 os.path.join(store_path, "audit.log"))
        raise PermissionError("Permission denied for 'restore' command")
    
    try:
        print(f"Restoring snapshot: {snapshot_id} to {target_path}")
        
        # 2. Load snapshot
        snapshot = load_snapshot(store_path, snapshot_id)
        
        # 3. Load manifest
        manifest = load_manifest(store_path, snapshot.manifest_hash)
        
        # 4. Verify Merkle root before restore
        print("Verifying snapshot integrity...")
        if not verify_merkle_root(manifest, snapshot.merkle_root):
            print(f"❌ RESTORE FAILED: Merkle root mismatch")
            log_audit("restore", [snapshot_id, target_path], "FAIL",
                     os.path.join(store_path, "audit.log"))
            return
        
        # 5. Create target directory
        os.makedirs(target_path, exist_ok=True)
        
        # 6. Restore files
        total_files = len(manifest["files"])
        for i, file_entry in enumerate(manifest["files"], 1):
            file_path = os.path.join(target_path, file_entry["path"])
            
            print(f"Restoring file {i}/{total_files}: {file_entry['path']}")
            
            # Create parent directories
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Restore file from chunks
            with open(file_path, 'wb') as f:
                for chunk_hash in file_entry["chunks"]:
                    chunk_data = get_chunk(store_path, chunk_hash)
                    f.write(chunk_data)
        
        # 7. Success
        print(f"✅ RESTORE OK: {snapshot_id} → {target_path}")
        print(f"Restored {total_files} file(s)")
        log_audit("restore", [snapshot_id, target_path], "OK",
                 os.path.join(store_path, "audit.log"))
        
    except FileNotFoundError as e:
        print(f"❌ RESTORE FAILED: {e}")
        log_audit("restore", [snapshot_id, target_path], "FAIL",
                 os.path.join(store_path, "audit.log"))
        raise
    except Exception as e:
        log_audit("restore", [snapshot_id, target_path], "FAIL",
                 os.path.join(store_path, "audit.log"))
        raise


def cmd_audit_verify(store_path: str) -> None:
    """
    Verify audit log integrity.
    
    Args:
        store_path: Path to backup store
    """
    from src.security.policy import check_permission
    from src.security.audit import verify_audit_log, log_audit
    
    # 1. Check permission
    if not check_permission("audit-verify"):
        log_audit("audit-verify", [], "DENY",
                 os.path.join(store_path, "audit.log"))
        raise PermissionError("Permission denied for 'audit-verify' command")
    
    try:
        # 2. Verify audit log
        audit_log_path = os.path.join(store_path, "audit.log")
        message, head_hash = verify_audit_log(audit_log_path)
        
        # 3. Print result
        print(message)
        if head_hash:
            print(f"Head hash: {head_hash}")
        
        # 4. Log audit
        status = "OK" if "OK" in message else "FAIL"
        log_audit("audit-verify", [], status,
                 os.path.join(store_path, "audit.log"))
        
    except Exception as e:
        log_audit("audit-verify", [], "FAIL",
                 os.path.join(store_path, "audit.log"))
        raise

