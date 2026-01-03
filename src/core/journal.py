"""
Journal/WAL module - MEMBER 3

Nhiệm vụ:
- Write-Ahead Logging cho crash consistency
- Format: BEGIN/WRITE/COMMIT
- Recovery: rollback uncommitted transactions
- PHẢI dùng fsync() để đảm bảo ghi xuống disk

Tham khảo: src/interfaces.py
"""

# TODO: Implement init_journal(), journal_begin(), journal_write(), journal_commit(), journal_recover()
