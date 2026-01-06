"""
Policy enforcement module - MEMBER 4

Nhiệm vụ:
- Load policy.yaml (YAML parsing)
- Check permission: user → role → allowed commands

Tham khảo: src/interfaces.py, policy.yaml
"""

# TODO: Implement load_policy(), check_permission()
import yaml
import os
from .user import get_current_user  # Import hàm lấy user từ user.py

# Đường dẫn file policy.yaml - bạn có thể thay đổi tùy cấu trúc project
DEFAULT_POLICY_PATH = "policy.yaml"  # Hoặc os.path.join("store", "policy.yaml")

_policy_cache = None  # Cache policy để không load lại nhiều lần

def load_policy(policy_path: str = DEFAULT_POLICY_PATH) -> dict:
    """
    Load và validate policy từ file YAML.
    Returns: dict với keys 'users' và 'roles'
    Raises: FileNotFoundError, ValueError nếu schema sai
    """
    global _policy_cache
    if _policy_cache is not None:
        return _policy_cache

    if not os.path.exists(policy_path):
        raise FileNotFoundError(f"Policy file not found: {policy_path}")

    with open(policy_path, 'r', encoding='utf-8') as f:
        policy = yaml.safe_load(f)

    # Validate schema cơ bản theo spec
    if not isinstance(policy, dict):
        raise ValueError("Policy must be a YAML mapping")

    if 'users' not in policy or 'roles' not in policy:
        raise ValueError("Policy must contain 'users' and 'roles' sections")

    if not isinstance(policy['users'], dict):
        raise ValueError("'users' must be a mapping os_username -> role")

    if not isinstance(policy['roles'], dict):
        raise ValueError("'roles' must be a mapping role -> list of commands")

    # Kiểm tra có đủ 3 role bắt buộc không (không bắt buộc phải có user nào)
    required_roles = {'admin', 'operator', 'auditor'}
    defined_roles = set(policy['roles'].keys())
    missing = required_roles - defined_roles
    if missing:
        raise ValueError(f"Missing required roles in policy: {missing}")

    _policy_cache = policy
    return policy


def get_current_role(policy: dict = None) -> str | None:
    """
    Lấy role của user hiện tại từ policy.
    Returns: role name (str) hoặc None nếu user không tồn tại trong policy
    """
    if policy is None:
        policy = load_policy()

    try:
        current_user = get_current_user()
    except ValueError:
        return None  # Không xác định được user → coi như không có quyền

    return policy['users'].get(current_user)


def check_permission(command: str, policy: dict = None) -> bool:
    """
    Kiểm tra user hiện tại có quyền chạy command không.
    Args:
        command: tên lệnh (init, backup, list-snapshots, verify, restore, audit-verify)
    Returns:
        True nếu được phép, False nếu bị từ chối (DENY)
    """
    if policy is None:
        policy = load_policy()

    role = get_current_role(policy)
    if role is None:
        return False  # User không có trong policy → DENY

    allowed_commands = policy['roles'].get(role, [])
    return command in allowed_commands


# Hàm tiện ích để CLI dùng (raise exception nếu không có quyền)
def enforce_permission(command: str, policy_path: str = DEFAULT_POLICY_PATH):
    """
    Kiểm tra quyền và raise PermissionError nếu bị từ chối.
    Dùng trong CLI trước khi thực hiện lệnh.
    """
    try:
        policy = load_policy(policy_path)
    except (FileNotFoundError, ValueError) as e:
        raise PermissionError(f"Policy error: {e}")

    if not check_permission(command, policy):
        current_user = "unknown"
        try:
            current_user = get_current_user()
        except:
            pass
        raise PermissionError(f"User '{current_user}' is not allowed to run command '{command}'")


# Test nhanh khi chạy file trực tiếp
def _test_policy():
    print("=== Policy Enforcement Test ===")
    try:
        policy = load_policy()
        print(f"Policy loaded successfully from {DEFAULT_POLICY_PATH}")

        user = get_current_user()
        role = get_current_role(policy)
        print(f"Current user: {user} -> role: {role}")

        test_commands = ["init", "backup", "restore", "audit-verify", "verify"]
        for cmd in test_commands:
            allowed = check_permission(cmd, policy)
            print(f"  {cmd}: {'ALLOWED' if allowed else 'DENIED'}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    _test_policy()