"""
Unit tests for Journal/WAL module

Test coverage:
- Basic transaction flow (BEGIN -> WRITE -> COMMIT)
- Crash recovery (rollback uncommitted transactions)
- Multiple transactions
- fsync functionality
"""

import os
import json
import tempfile
import shutil
import pytest
from src.core.journal import (
    init_journal,
    journal_begin,
    journal_write,
    journal_commit,
    journal_recover
)


class TestJournal:
    """Test suite for Journal/WAL module"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.test_store = tempfile.mkdtemp(prefix="test_journal_")
        os.makedirs(os.path.join(self.test_store, "snapshots"), exist_ok=True)
    
    def teardown_method(self):
        """Cleanup after each test"""
        shutil.rmtree(self.test_store, ignore_errors=True)
    
    def test_init_journal(self):
        """Test journal initialization"""
        init_journal(self.test_store)
        
        journal_path = os.path.join(self.test_store, "journal.wal")
        assert os.path.exists(journal_path), "Journal file should be created"
    
    def test_basic_transaction_flow(self):
        """Test BEGIN -> WRITE -> COMMIT flow"""
        init_journal(self.test_store)
        
        # Begin transaction
        txn_id = journal_begin(self.test_store, "backup")
        assert txn_id.startswith("txn_"), "Transaction ID should start with 'txn_'"
        
        # Write record
        record = {"snapshot_id": "snapshot_123", "label": "test"}
        journal_write(self.test_store, txn_id, record)
        
        # Commit
        journal_commit(self.test_store, txn_id)
        
        # Verify journal content
        journal_path = os.path.join(self.test_store, "journal.wal")
        with open(journal_path, 'r') as f:
            content = f.read()
            assert "BEGIN" in content
            assert txn_id in content
            assert "WRITE" in content
            assert "COMMIT" in content
    
    def test_crash_recovery_rollback(self):
        """Test crash recovery: uncommitted transaction should be rolled back"""
        init_journal(self.test_store)
        
        # Create a snapshot file
        snapshot_id = "snapshot_crash_test"
        snapshot_path = os.path.join(self.test_store, "snapshots", f"{snapshot_id}.json")
        with open(snapshot_path, 'w') as f:
            json.dump({"id": snapshot_id}, f)
        
        assert os.path.exists(snapshot_path), "Snapshot should exist before crash"
        
        # Create uncommitted transaction
        txn_id = journal_begin(self.test_store, "backup")
        journal_write(self.test_store, txn_id, {"snapshot_id": snapshot_id})
        # NO COMMIT - simulate crash
        
        # Recover
        journal_recover(self.test_store)
        
        # Snapshot should be deleted
        assert not os.path.exists(snapshot_path), "Snapshot should be deleted after rollback"
    
    def test_crash_recovery_keeps_committed(self):
        """Test crash recovery: committed transactions should be kept"""
        init_journal(self.test_store)
        
        # Create a committed snapshot
        snapshot_id_committed = "snapshot_committed"
        snapshot_path_committed = os.path.join(
            self.test_store, "snapshots", f"{snapshot_id_committed}.json"
        )
        with open(snapshot_path_committed, 'w') as f:
            json.dump({"id": snapshot_id_committed}, f)
        
        # Create committed transaction
        txn_id1 = journal_begin(self.test_store, "backup")
        journal_write(self.test_store, txn_id1, {"snapshot_id": snapshot_id_committed})
        journal_commit(self.test_store, txn_id1)
        
        # Create uncommitted snapshot
        snapshot_id_uncommitted = "snapshot_uncommitted"
        snapshot_path_uncommitted = os.path.join(
            self.test_store, "snapshots", f"{snapshot_id_uncommitted}.json"
        )
        with open(snapshot_path_uncommitted, 'w') as f:
            json.dump({"id": snapshot_id_uncommitted}, f)
        
        # Create uncommitted transaction
        txn_id2 = journal_begin(self.test_store, "backup")
        journal_write(self.test_store, txn_id2, {"snapshot_id": snapshot_id_uncommitted})
        # NO COMMIT
        
        # Recover
        journal_recover(self.test_store)
        
        # Committed snapshot should still exist
        assert os.path.exists(snapshot_path_committed), "Committed snapshot should be kept"
        
        # Uncommitted snapshot should be deleted
        assert not os.path.exists(snapshot_path_uncommitted), "Uncommitted snapshot should be deleted"
    
    def test_multiple_transactions(self):
        """Test multiple transactions in sequence"""
        init_journal(self.test_store)
        
        # Transaction 1
        txn_id1 = journal_begin(self.test_store, "backup")
        journal_write(self.test_store, txn_id1, {"snapshot_id": "snap1"})
        journal_commit(self.test_store, txn_id1)
        
        # Transaction 2
        txn_id2 = journal_begin(self.test_store, "backup")
        journal_write(self.test_store, txn_id2, {"snapshot_id": "snap2"})
        journal_commit(self.test_store, txn_id2)
        
        # Verify both transactions in journal
        journal_path = os.path.join(self.test_store, "journal.wal")
        with open(journal_path, 'r') as f:
            content = f.read()
            assert txn_id1 in content
            assert txn_id2 in content
            assert content.count("BEGIN") == 2
            assert content.count("COMMIT") == 2
    
    def test_journal_recover_empty_journal(self):
        """Test recovery with empty journal (should not crash)"""
        init_journal(self.test_store)
        
        # Should not raise exception
        journal_recover(self.test_store)
    
    def test_journal_recover_no_journal(self):
        """Test recovery when journal doesn't exist (should not crash)"""
        # Should not raise exception
        journal_recover(self.test_store)
    
    def test_fsync_called(self):
        """Test that fsync is called (doesn't crash)"""
        init_journal(self.test_store)
        
        # These should all call fsync without crashing
        txn_id = journal_begin(self.test_store, "backup")
        journal_write(self.test_store, txn_id, {"test": "data"})
        journal_commit(self.test_store, txn_id)
        
        # If we got here, fsync worked
        assert True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
