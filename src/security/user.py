"""
User identification module - MEMBER 4

Nhiệm vụ:
- Lấy OS username
- Ưu tiên SUDO_USER nếu có
- Windows: DOMAIN\\Username hoặc Username

Tham khảo: src/interfaces.py
"""

# TODO: Implement get_current_user()
import os
import platform

def get_current_user() -> str:
    # 1. Ưu tiên SUDO_USER (spec: "nếu môi trường có SUDO_USER, bắt buộc dùng")
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return sudo_user
    
    # 2. Fallback theo platform
    system = platform.system().lower()
    
    if system == "linux" or system == "darwin":  # Linux/macOS
        try:
            # Thử getlogin() trước (an toàn nhất cho CLI)
            username = os.getlogin()
            if username:
                return username
        except OSError:
            pass
        
        # Fallback env vars
        username = os.environ.get("USER") or os.environ.get("LOGNAME")
        if username:
            return username
    
    elif system == "windows":
        username = os.environ.get("USERNAME")
        if not username:
            username = os.environ.get("USER")
        
        if username:
            # Kiểm tra domain (DOMAIN\Username format)
            domain = os.environ.get("USERDOMAIN") or os.environ.get("COMPUTERNAME")
            if domain and domain != username.upper():  # Tránh trùng COMPUTERNAME
                return f"{domain}\\{username}"
            return username
    
    # 3. Nếu tất cả fail -> từ chối (ghi audit FAIL)
    raise ValueError("Cannot determine current OS user (no TTY/SUDO_USER/USERNAME)")

# Test function (dùng trong tests/test_security/test_all.py)
def test_get_current_user():
    """Test đơn giản cho module"""
    try:
        user = get_current_user()
        print(f"Current user: {user}")
        return True
    except ValueError as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Chạy test nhanh
    print("=== User Identification Test ===")
    success = test_get_current_user()
    print(f"Test {'PASS' if success else 'FAIL'}")