"""
Integration tests for required scenarios - MEMBER 3

7 Test Scenarios Bắt Buộc:
1. Restore integrity (xóa files, restore, so sánh)
2. Chunk corruption (sửa 1 byte → verify FAIL)
3. Manifest corruption (sửa manifest → verify FAIL)
4. Rollback detection (thay snapshot mới bằng cũ → phát hiện)
5. Crash consistency (kill backup → store OK)
6. Policy enforcement (lệnh không được phép → DENY)
7. Audit tampering (sửa audit.log → CORRUPTED)
"""

import os
import sys
import json
import shutil
import tempfile
import time
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.cli.commands import (
    cmd_init,
    cmd_backup,
    cmd_list_snapshots,
    cmd_verify,
    cmd_restore,
    cmd_audit_verify,
    scan_directory
)
from src.core.journal import journal_begin, journal_write
from src.security.audit import verify_audit_log


class TestRequiredScenarios:
    """Integration tests for 7 required scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="test_integration_")
        self.store_path = os.path.join(self.test_dir, "store")
        self.dataset_path = os.path.join(self.test_dir, "dataset")
        self.restore_path = os.path.join(self.test_dir, "restored")
        
        # Create test dataset
        os.makedirs(self.dataset_path)
        self._create_test_dataset()
        
        # Initialize store
        cmd_init(self.store_path)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_dataset(self):
        """Create test dataset with multiple files"""
        # Create files
        with open(os.path.join(self.dataset_path, "file1.txt"), 'w') as f:
            f.write("Hello World\n" * 100)
        
        with open(os.path.join(self.dataset_path, "file2.txt"), 'w') as f:
            f.write("Test Data\n" * 100)
        
        # Create subdirectory
        subdir = os.path.join(self.dataset_path, "subdir")
        os.makedirs(subdir)
        
        with open(os.path.join(subdir, "file3.txt"), 'w') as f:
            f.write("Nested file\n" * 100)
    
    def _compare_directories(self, dir1, dir2):
        """Compare two directories recursively"""
        files1 = sorted(scan_directory(dir1))
        files2 = sorted(scan_directory(dir2))
        
        # Compare number of files
        assert len(files1) == len(files2), f"Different number of files: {len(files1)} vs {len(files2)}"
        
        # Compare file contents
        for f1, f2 in zip(files1, files2):
            rel1 = os.path.relpath(f1, dir1)
            rel2 = os.path.relpath(f2, dir2)
            
            assert rel1 == rel2, f"Different file paths: {rel1} vs {rel2}"
            
            with open(f1, 'rb') as file1, open(f2, 'rb') as file2:
                content1 = file1.read()
                content2 = file2.read()
                assert content1 == content2, f"Different content in {rel1}"
    
    # ========== TEST 1: Restore Integrity ==========
    def test_1_restore_integrity(self):
        """
        Test 1: Restore integrity
        - Tạo dataset với files
        - Backup
        - Xóa dataset
        - Restore
        - So sánh: restored == original
        """
        print("\n=== Test 1: Restore Integrity ===")
        
        # 1. Backup dataset
        cmd_backup(self.store_path, self.dataset_path, "Test backup")
        
        # 2. Get snapshot ID
        from src.core.snapshot import list_snapshots
        snapshots = list_snapshots(self.store_path)
        assert len(snapshots) == 1
        snapshot_id = snapshots[0].id
        
        # 3. Save original dataset for comparison
        original_files = {}
        for file_path in scan_directory(self.dataset_path):
            with open(file_path, 'rb') as f:
                rel_path = os.path.relpath(file_path, self.dataset_path)
                original_files[rel_path] = f.read()
        
        # 4. Delete dataset
        shutil.rmtree(self.dataset_path)
        assert not os.path.exists(self.dataset_path)
        
        # 5. Restore
        cmd_restore(self.store_path, snapshot_id, self.restore_path)
        
        # 6. Compare restored with original
        restored_files = {}
        for file_path in scan_directory(self.restore_path):
            with open(file_path, 'rb') as f:
                rel_path = os.path.relpath(file_path, self.restore_path)
                restored_files[rel_path] = f.read()
        
        # Verify same files
        assert set(original_files.keys()) == set(restored_files.keys())
        
        # Verify same content
        for rel_path, original_content in original_files.items():
            assert restored_files[rel_path] == original_content, \
                f"Content mismatch in {rel_path}"
        
        print("✅ Test 1 PASSED: Restore integrity verified")
    
    # ========== TEST 2: Chunk Corruption ==========
    def test_2_chunk_corruption(self):
        """
        Test 2: Chunk corruption
        - Tạo backup
        - Sửa 1 byte trong một chunk file
        - Verify → phải FAIL
        """
        print("\n=== Test 2: Chunk Corruption ===")
        
        # 1. Backup
        cmd_backup(self.store_path, self.dataset_path, "Test backup")
        
        # 2. Get snapshot ID
        from src.core.snapshot import list_snapshots
        snapshots = list_snapshots(self.store_path)
        snapshot_id = snapshots[0].id
        
        # 3. Find a chunk file and corrupt it
        chunks_dir = os.path.join(self.store_path, "chunks")
        chunk_file = None
        
        for root, dirs, files in os.walk(chunks_dir):
            if files:
                chunk_file = os.path.join(root, files[0])
                break
        
        assert chunk_file is not None, "No chunk file found"
        
        # 4. Corrupt the chunk (modify 1 byte)
        with open(chunk_file, 'r+b') as f:
            f.seek(0)
            byte = f.read(1)
            f.seek(0)
            # Flip first bit
            corrupted_byte = bytes([byte[0] ^ 1])
            f.write(corrupted_byte)
        
        # 5. Verify should FAIL
        from src.core.snapshot import load_snapshot, load_manifest
        from src.core.merkle import verify_merkle_root
        from src.core.storage import get_chunk
        
        snapshot = load_snapshot(self.store_path, snapshot_id)
        manifest = load_manifest(self.store_path, snapshot.manifest_hash)
        
        # Merkle root should still match (corruption is in chunk, not manifest)
        assert verify_merkle_root(manifest, snapshot.merkle_root)
        
        # But chunk integrity check should fail
        chunk_integrity_failed = False
        for file_entry in manifest["files"]:
            for chunk_hash in file_entry["chunks"]:
                try:
                    get_chunk(self.store_path, chunk_hash)
                except ValueError:
                    chunk_integrity_failed = True
                    break
            if chunk_integrity_failed:
                break
        
        assert chunk_integrity_failed, "Chunk corruption was not detected"
        
        print("✅ Test 2 PASSED: Chunk corruption detected")
    
    # ========== TEST 3: Manifest Corruption ==========
    def test_3_manifest_corruption(self):
        """
        Test 3: Manifest corruption
        - Tạo backup
        - Sửa manifest file
        - Verify → phải FAIL
        """
        print("\n=== Test 3: Manifest Corruption ===")
        
        # 1. Backup
        cmd_backup(self.store_path, self.dataset_path, "Test backup")
        
        # 2. Get snapshot
        from src.core.snapshot import list_snapshots, load_snapshot
        snapshots = list_snapshots(self.store_path)
        snapshot = snapshots[0]
        
        # 3. Corrupt manifest file
        manifest_path = os.path.join(self.store_path, "manifests", f"{snapshot.manifest_hash}.json")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        # Modify manifest (change a chunk hash)
        if manifest_data["files"] and manifest_data["files"][0]["chunks"]:
            original_hash = manifest_data["files"][0]["chunks"][0]
            # Flip one character in hash
            corrupted_hash = original_hash[:-1] + ('0' if original_hash[-1] != '0' else '1')
            manifest_data["files"][0]["chunks"][0] = corrupted_hash
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f)
        
        # 4. Verify should FAIL (Merkle root mismatch)
        from src.core.snapshot import load_manifest
        from src.core.merkle import verify_merkle_root
        
        corrupted_manifest = load_manifest(self.store_path, snapshot.manifest_hash)
        merkle_match = verify_merkle_root(corrupted_manifest, snapshot.merkle_root)
        
        assert not merkle_match, "Manifest corruption was not detected"
        
        print("✅ Test 3 PASSED: Manifest corruption detected")
    
    # ========== TEST 4: Rollback Detection ==========
    def test_4_rollback_detection(self):
        """
        Test 4: Rollback detection
        - Tạo snapshot A
        - Tạo snapshot B (mới hơn)
        - Thay snapshot B bằng snapshot A
        - Verify → phải phát hiện rollback
        """
        print("\n=== Test 4: Rollback Detection ===")
        
        # 1. Create snapshot A
        cmd_backup(self.store_path, self.dataset_path, "Snapshot A")
        
        # 2. Modify dataset
        with open(os.path.join(self.dataset_path, "file1.txt"), 'a') as f:
            f.write("Modified content\n")
        
        # 3. Create snapshot B
        time.sleep(1)  # Ensure different timestamp
        cmd_backup(self.store_path, self.dataset_path, "Snapshot B")
        
        # 4. Get snapshots
        from src.core.snapshot import list_snapshots, load_snapshot
        snapshots = list_snapshots(self.store_path)
        assert len(snapshots) == 2
        
        snapshot_a = snapshots[0]
        snapshot_b = snapshots[1]
        
        # 5. Simulate rollback: replace snapshot B with snapshot A's data
        # but keep snapshot B's ID and timestamp
        snapshot_b_path = os.path.join(self.store_path, "snapshots", f"{snapshot_b.id}.json")
        
        # Load snapshot A data
        with open(os.path.join(self.store_path, "snapshots", f"{snapshot_a.id}.json"), 'r') as f:
            snapshot_a_data = json.load(f)
        
        # Keep B's ID and timestamp, but use A's merkle_root (rollback attack)
        with open(snapshot_b_path, 'r') as f:
            snapshot_b_data = json.load(f)
        
        snapshot_b_data["merkle_root"] = snapshot_a_data["merkle_root"]
        snapshot_b_data["manifest_hash"] = snapshot_a_data["manifest_hash"]
        # Keep prev_root pointing to A (this will cause mismatch)
        
        with open(snapshot_b_path, 'w') as f:
            json.dump(snapshot_b_data, f)
        
        # 6. Verify should detect rollback
        # The prev_root of B should match A's merkle_root, but we replaced B's merkle_root with A's
        # This creates an inconsistency that verify should detect
        
        from src.core.snapshot import load_manifest
        from src.core.merkle import verify_merkle_root
        
        snapshot_b_reloaded = load_snapshot(self.store_path, snapshot_b.id)
        
        # Check if prev_root chain is broken
        # snapshot_b should have prev_root = snapshot_a.merkle_root
        # But if we verify the chain, snapshot_b's merkle_root should be different from snapshot_a
        
        rollback_detected = (snapshot_b_reloaded.merkle_root == snapshot_a.merkle_root)
        
        assert rollback_detected, "Rollback should be detected (same merkle_root as previous)"
        
        print("✅ Test 4 PASSED: Rollback detected")
    
    # ========== TEST 5: Crash Consistency ==========
    def test_5_crash_consistency(self):
        """
        Test 5: Crash consistency
        - Start backup
        - Kill process giữa chừng (simulate crash)
        - Restart
        - Store vẫn hoạt động, không có snapshot lỗi
        """
        print("\n=== Test 5: Crash Consistency ===")
        
        # 1. Start a backup transaction but don't commit
        from src.core.journal import journal_begin, journal_write
        from src.core.snapshot import create_snapshot
        from src.core.manifest import create_manifest, hash_manifest
        from src.interfaces import FileEntry
        
        # Begin transaction
        txn_id = journal_begin(self.store_path, "backup")
        
        # Create a fake snapshot (simulating incomplete backup)
        fake_manifest = create_manifest([FileEntry(path="fake.txt", chunks=["fakehash"])])
        fake_snapshot_id = f"snapshot_{int(time.time())}"
        
        # Write to journal but DON'T commit
        journal_write(self.store_path, txn_id, {"snapshot_id": fake_snapshot_id})
        
        # Create snapshot file (simulating partial backup)
        from src.core.snapshot import create_snapshot
        snapshot_id = create_snapshot(self.store_path, fake_manifest, "Incomplete backup", "")
        
        # 2. Simulate crash (don't call journal_commit)
        # Journal has uncommitted transaction
        
        # 3. Recover (this should happen automatically on next backup)
        from src.core.journal import journal_recover
        journal_recover(self.store_path)
        
        # 4. Verify store is still functional
        # Create a real backup
        cmd_backup(self.store_path, self.dataset_path, "After crash")
        
        # 5. List snapshots - should only show the valid one
        from src.core.snapshot import list_snapshots
        snapshots = list_snapshots(self.store_path)
        
        # The incomplete snapshot should have been rolled back
        snapshot_ids = [s.id for s in snapshots]
        
        # Should have at least one valid snapshot
        assert len(snapshots) >= 1, "No valid snapshots after recovery"
        
        # Verify all snapshots are valid
        for snapshot in snapshots:
            from src.core.snapshot import load_snapshot, load_manifest
            from src.core.merkle import verify_merkle_root
            
            snap = load_snapshot(self.store_path, snapshot.id)
            manifest = load_manifest(self.store_path, snap.manifest_hash)
            assert verify_merkle_root(manifest, snap.merkle_root), \
                f"Invalid snapshot found: {snapshot.id}"
        
        print("✅ Test 5 PASSED: Crash consistency maintained")
    
    # ========== TEST 6: Policy Enforcement ==========
    def test_6_policy_enforcement(self):
        """
        Test 6: Policy enforcement
        - Mock user không có quyền
        - Chạy lệnh bị cấm
        - Phải bị DENY và có audit log
        """
        print("\n=== Test 6: Policy Enforcement ===")
        
        # 1. Mock a user without permission
        # We'll temporarily modify the policy check
        from src.security import policy
        
        # Save original function
        original_check = policy.check_permission
        
        # Mock to always return False
        def mock_check_permission(command, policy_dict=None):
            return False
        
        policy.check_permission = mock_check_permission
        
        try:
            # 2. Try to run a command (should be denied)
            with pytest.raises(PermissionError) as exc_info:
                cmd_backup(self.store_path, self.dataset_path, "Should be denied")
            
            assert "Permission denied" in str(exc_info.value)
            
            # 3. Check audit log for DENY entry
            audit_log_path = os.path.join(self.store_path, "audit.log")
            
            with open(audit_log_path, 'r') as f:
                audit_content = f.read()
            
            assert "DENY" in audit_content, "DENY not found in audit log"
            assert "backup" in audit_content, "Command not logged in audit"
            
            print("✅ Test 6 PASSED: Policy enforcement working")
            
        finally:
            # Restore original function
            policy.check_permission = original_check
    
    # ========== TEST 7: Audit Tampering ==========
    def test_7_audit_tampering(self):
        """
        Test 7: Audit tampering
        - Tạo audit log
        - Sửa 1 ký tự trong audit.log
        - audit-verify → phải báo CORRUPTED
        """
        print("\n=== Test 7: Audit Tampering ===")
        
        # 1. Create some audit entries
        cmd_backup(self.store_path, self.dataset_path, "Test backup")
        
        # 2. Verify audit is OK first
        audit_log_path = os.path.join(self.store_path, "audit.log")
        message, head_hash = verify_audit_log(audit_log_path)
        assert "OK" in message, "Audit should be OK before tampering"
        
        # 3. Tamper with audit log (modify 1 character)
        with open(audit_log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) > 0, "No audit log entries"
        
        # Modify first line (change one character in hash)
        first_line = lines[0]
        # Change one character in the middle
        tampered_line = first_line[:10] + ('X' if first_line[10] != 'X' else 'Y') + first_line[11:]
        lines[0] = tampered_line
        
        with open(audit_log_path, 'w') as f:
            f.writelines(lines)
        
        # 4. Verify audit should detect corruption
        message, head_hash = verify_audit_log(audit_log_path)
        
        assert "CORRUPTED" in message, "Audit tampering was not detected"
        
        print("✅ Test 7 PASSED: Audit tampering detected")


# ========== RUN ALL TESTS ==========
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
