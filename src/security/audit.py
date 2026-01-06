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

import hashlib
import time
import os
from .user import get_current_user

# Đường dẫn audit log - bạn có thể thay đổi (gợi ý đặt trong store/)
DEFAULT_AUDIT_LOG_PATH = "store/audit.log"

# Hash khởi tạo cho dòng đầu tiên (64 ký tự 0)
INITIAL_PREV_HASH = "0" * 64


def _compute_sha256(data: str) -> str:
    """Tính SHA-256 hex digest"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def _get_prev_hash(log_path: str) -> str:
    """Lấy ENTRY_HASH của dòng cuối cùng làm PREV_HASH cho dòng mới"""
    if not os.path.exists(log_path):
        return INITIAL_PREV_HASH
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if not lines:
            return INITIAL_PREV_HASH
        last_line = lines[-1].strip()
        if not last_line:
            return INITIAL_PREV_HASH
        return last_line.split()[0]  # ENTRY_HASH của dòng trước


def log_audit(command: str, args: list[str], status: str, log_path: str = DEFAULT_AUDIT_LOG_PATH) -> None:
    """
    Ghi một entry vào audit log (append-only + hash chain)
    
    Args:
        command: tên lệnh (init, backup, verify, restore, audit-verify, ...)
        args: list các argument (không bao gồm tên lệnh)
        status: "OK" | "DENY" | "FAIL"
        log_path: đường dẫn file audit log
    """
    assert status in {"OK", "DENY", "FAIL"}, "STATUS must be OK, DENY or FAIL"

    try:
        user = get_current_user()
    except ValueError:
        user = "unknown"

    unix_ms = int(time.time() * 1000)

    # Tính ARGS_SHA256: join args bằng space (theo khuyến nghị đề bài)
    args_str = " ".join(args)
    args_sha256 = _compute_sha256(args_str)

    # Lấy PREV_HASH
    prev_hash = _get_prev_hash(log_path)

    # Nội dung dùng để tính ENTRY_HASH (không có ENTRY_HASH)
    content = f"{prev_hash} {unix_ms} {user} {command} {args_sha256} {status}"
    entry_hash = _compute_sha256(content)

    # Dòng đầy đủ ghi vào file
    log_line = f"{entry_hash} {content}\n"

    # Tạo thư mục nếu chưa có
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Append-only
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_line)


def verify_audit_log(log_path: str = DEFAULT_AUDIT_LOG_PATH) -> tuple[str, str | None]:
    """
    Kiểm tra tính toàn vẹn của audit log (hash chain)
    
    Returns:
        (message, head_hash)
        - Nếu OK: ("AUDIT OK", last_entry_hash)
        - Nếu lỗi: ("AUDIT CORRUPTED: <lý do> at line X", None)
    """
    if not os.path.exists(log_path):
        return "AUDIT OK (empty log)", None

    with open(log_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if not lines:
        return "AUDIT OK (empty log)", None

    expected_prev_hash = INITIAL_PREV_HASH

    for i, line in enumerate(lines, start=1):
        parts = line.split()
        if len(parts) != 7:
            return f"AUDIT CORRUPTED: Invalid format (expected 7 fields) at line {i}", None

        entry_hash, prev_hash, unix_ms_str, user, command, args_sha256, status = parts

        # Kiểm tra prev_hash có khớp với expected không
        if prev_hash != expected_prev_hash:
            return f"AUDIT CORRUPTED: Previous hash mismatch at line {i}", None

        # Tính lại entry_hash từ content
        content = f"{prev_hash} {unix_ms_str} {user} {command} {args_sha256} {status}"
        computed_hash = _compute_sha256(content)

        if computed_hash != entry_hash:
            return f"AUDIT CORRUPTED: Entry hash mismatch at line {i}", None

        # Cập nhật expected_prev_hash cho dòng tiếp theo
        expected_prev_hash = entry_hash

    # Nếu tất cả OK
    return "AUDIT OK", expected_prev_hash


# Test nhanh khi chạy file trực tiếp
def _test_audit():
    print("=== Audit Log Test ===")
    log_path = "test_audit.log"

    # Xóa file test cũ nếu có
    if os.path.exists(log_path):
        os.remove(log_path)

    # Ghi vài entry
    log_audit("init", ["store/"], "OK", log_path)
    log_audit("backup", ["dataset/", "--label", "test1"], "OK", log_path)
    log_audit("restore", ["snap123", "out/"], "DENY", log_path)

    msg, head = verify_audit_log(log_path)
    print(msg)
    if head:
        print(f"Head hash: {head}")

    # Test tamper: sửa 1 byte
    print("\n--- Tamper test ---")
    with open(log_path, 'a') as f:
        f.write("TAMPER\n")  # Thêm dòng lỗi

    msg, _ = verify_audit_log(log_path)
    print(msg)

    # Dọn dẹp
    os.remove(log_path)


if __name__ == "__main__":
    _test_audit()