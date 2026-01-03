"""
Audit logging module - MEMBER 4

Nhiệm vụ:
- Append-only audit log với hash chain
- Format: ENTRY_HASH PREV_HASH UNIX_MS USER COMMAND ARGS_SHA256 STATUS
- ENTRY_HASH = SHA256(PREV_HASH + UNIX_MS + USER + COMMAND + ARGS_SHA256 + STATUS)
- Verify: phát hiện sửa/xóa/chèn log

Tham khảo: src/interfaces.py, yêu cầu đề bài
"""

# TODO: Implement init_audit_log(), log_audit(), verify_audit_log()
