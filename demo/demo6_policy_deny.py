"""
Demo 6: Policy Enforcement - DENY Command

Kịch bản:
1. Show role hiện tại của OS user
2. Tạm thời thay đổi role thành 'auditor' trong policy.yaml
3. Thử chạy lệnh 'init' (auditor không có quyền)
4. Lệnh bị DENY và có audit log
5. Khôi phục lại role ban đầu

Kết quả mong đợi: Lệnh bị từ chối và có DENY entry trong audit log
"""

import os
import sys
import shutil
import yaml

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.security.user import get_current_user
from src.security.policy import load_policy, get_current_role, check_permission
from src.cli.commands import cmd_init
from src.security.audit import verify_audit_log


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def backup_policy():
    """Backup current policy.yaml"""
    if os.path.exists("policy.yaml"):
        shutil.copy("policy.yaml", "policy.yaml.backup")
        return True
    return False


def restore_policy():
    """Restore original policy.yaml"""
    if os.path.exists("policy.yaml.backup"):
        shutil.copy("policy.yaml.backup", "policy.yaml")
        os.remove("policy.yaml.backup")
        return True
    return False


def modify_user_role(username, new_role):
    """Modify user's role in policy.yaml"""
    with open("policy.yaml", 'r', encoding='utf-8') as f:
        policy = yaml.safe_load(f)
    
    old_role = policy['users'].get(username, None)
    policy['users'][username] = new_role
    
    with open("policy.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(policy, f, default_flow_style=False, allow_unicode=True)
    
    # Clear policy cache
    import src.security.policy as policy_module
    policy_module._policy_cache = None
    
    return old_role


def main():
    print("=" * 80)
    print("DEMO 6: Policy Enforcement - DENY Command")
    print("=" * 80)
    
    store_path = "store"
    original_role = None
    current_user = None
    
    try:
        # Step 1: Show current user and role
        print_section("STEP 1: Check Current User and Role")
        
        current_user = get_current_user()
        print(f"👤 Current OS User: {current_user}")
        
        policy = load_policy()
        original_role = get_current_role(policy)
        
        if not original_role:
            print(f"❌ User '{current_user}' not found in policy.yaml")
            print("\n💡 Please add your user to policy.yaml:")
            print(f"   users:")
            print(f"     {current_user}: admin")
            return 1
        
        print(f"🎭 Current Role: {original_role}")
        
        # Show allowed commands
        allowed_commands = policy['roles'].get(original_role, [])
        print(f"\n📋 Allowed commands for role '{original_role}':")
        for cmd in allowed_commands:
            print(f"   ✓ {cmd}")
        
        # Step 2: Backup and modify policy
        print_section("STEP 2: Temporarily Change Role to 'auditor'")
        
        print(f"💾 Backing up policy.yaml...")
        backup_policy()
        
        print(f"🔧 Changing role: {original_role} → auditor")
        modify_user_role(current_user, 'auditor')
        
        # Reload policy
        import src.security.policy as policy_module
        policy_module._policy_cache = None
        new_policy = load_policy()
        new_role = get_current_role(new_policy)
        
        print(f"✅ Role changed successfully to: {new_role}")
        
        # Show new permissions
        new_allowed = new_policy['roles'].get(new_role, [])
        print(f"\n📋 Allowed commands for role '{new_role}':")
        for cmd in new_allowed:
            print(f"   ✓ {cmd}")
        
        denied_commands = ['init', 'backup']
        denied_for_auditor = [cmd for cmd in denied_commands if cmd not in new_allowed]
        if denied_for_auditor:
            print(f"\n🚫 Denied commands for role '{new_role}':")
            for cmd in denied_for_auditor:
                print(f"   ✗ {cmd}")
        
        # Step 3: Try denied command
        print_section("STEP 3: Try Running Denied Command 'init'")
        
        # Ensure store exists for audit log
        os.makedirs(store_path, exist_ok=True)
        
        # Clear audit log for clean test
        audit_log_path = os.path.join(store_path, "audit.log")
        if os.path.exists(audit_log_path):
            # Backup audit log
            shutil.copy(audit_log_path, audit_log_path + ".backup")
            os.remove(audit_log_path)
            print("🧹 Cleared audit log for clean demo")
        
        print(f"\n🧪 Testing command: init")
        print(f"👤 Current role: {new_role}")
        
        # Check permission
        has_permission = check_permission("init")
        print(f"🔍 Permission check: {'ALLOWED ✓' if has_permission else 'DENIED ✗'}")
        
        if has_permission:
            print("❌ Unexpected: Auditor should not have 'init' permission!")
            restore_policy()
            return 1
        
        # Try to execute
        print(f"\n🚀 Attempting to execute 'init' command...")
        
        try:
            cmd_init(store_path)
            print(f"❌ UNEXPECTED: Command executed successfully!")
            restore_policy()
            return 1
        except PermissionError as e:
            print(f"✅ Command DENIED as expected!")
            print(f"   Error: {e}")
        
        # Step 4: Verify audit log
        print_section("STEP 4: Verify DENY Entry in Audit Log")
        
        if not os.path.exists(audit_log_path):
            print(f"❌ Audit log not found!")
            restore_policy()
            return 1
        
        with open(audit_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📄 Audit log has {len(lines)} entry(ies)")
        
        # Find DENY entry
        deny_found = False
        for i, line in enumerate(lines, 1):
            if 'DENY' in line:
                deny_found = True
                print(f"\n✅ Found DENY entry at line {i}:")
                parts = line.strip().split()
                if len(parts) >= 7:
                    print(f"   User: {parts[3]}")
                    print(f"   Command: {parts[4]}")
                    print(f"   Status: {parts[6]}")
                    print(f"   Entry hash: {parts[0][:16]}...")
        
        if not deny_found:
            print("❌ No DENY entry found!")
            restore_policy()
            return 1
        
        # Verify audit integrity
        print(f"\n🔍 Verifying audit log integrity...")
        message, head_hash = verify_audit_log(audit_log_path)
        print(f"   {message}")
        if head_hash:
            print(f"   Head hash: {head_hash[:16]}...")
        
        # Restore audit log
        if os.path.exists(audit_log_path + ".backup"):
            os.remove(audit_log_path)
            shutil.copy(audit_log_path + ".backup", audit_log_path)
            os.remove(audit_log_path + ".backup")
            print(f"\n✅ Restored original audit log")
        
        # Success
        print_section("DEMO 6 COMPLETE - SUCCESS")
        print(f"✅ Original role: {original_role}")
        print(f"✅ Temporarily changed to: auditor")
        print(f"✅ Command 'init' denied (PermissionError)")
        print(f"✅ DENY entry logged in audit log")
        print(f"✅ Audit log integrity verified")
        print("\n🎉 Policy enforcement working correctly!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Always restore policy
        if original_role and current_user:
            print_section("STEP 5: Restore Original Role")
            print(f"🔄 Restoring role: auditor → {original_role}")
            restore_policy()
            print(f"✅ Role restored to: {original_role}")


if __name__ == "__main__":
    sys.exit(main())
