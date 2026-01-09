"""
Demo 7: Audit Log Tampering Detection

Kịch bản:
1. Tạo audit log entries hợp lệ
2. Verify audit log → OK
3. Sửa 1 ký tự trong audit.log
4. Verify audit log → CORRUPTED
5. Khôi phục và xóa 1 dòng
6. Verify audit log → CORRUPTED

Kết quả mong đợi: Audit verify phát hiện mọi thay đổi
"""

import os
import sys
import shutil

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.commands import cmd_audit_verify
from src.security.audit import verify_audit_log


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print("=" * 80)
    print("DEMO 7: Audit Log Tampering Detection")
    print("=" * 80)
    
    store_path = "store"
    audit_log_path = os.path.join(store_path, "audit.log")
    
    # Check prerequisites
    if not os.path.exists(audit_log_path):
        print(f"❌ Audit log not found at {audit_log_path}")
        print("Please run some commands first to generate audit log")
        return 1
    
    try:
        # Step 1: Verify audit log is OK
        print_section("STEP 1: Verify Audit Log (Before Tampering)")
        
        message, head_hash = verify_audit_log(audit_log_path)
        print(f"Status: {message}")
        if head_hash:
            print(f"Head hash: {head_hash[:16]}...")
        
        if "OK" not in message:
            print("❌ Audit log is already corrupted!")
            return 1
        
        print("✅ Audit log is valid (before tampering)")
        
        # Backup audit log
        audit_backup = audit_log_path + ".backup"
        shutil.copy(audit_log_path, audit_backup)
        print(f"💾 Backed up audit log to: {audit_backup}")
        
        # Read original
        with open(audit_log_path, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
        
        print(f"📄 Audit log has {len(original_lines)} entries")
        
        # Step 2: Tamper - modify 1 character
        print_section("STEP 2: Tamper - Modify 1 Character")
        
        if len(original_lines) == 0:
            print("❌ Audit log is empty!")
            return 1
        
        print("Modifying first line (changing 1 character in hash)...")
        
        first_line = original_lines[0]
        print(f"Original first line (first 60 chars):")
        print(f"   {first_line[:60]}...")
        
        # Change one character at position 10
        tampered_line = first_line[:10] + ('X' if first_line[10] != 'X' else 'Y') + first_line[11:]
        original_lines[0] = tampered_line
        
        print(f"Tampered first line (first 60 chars):")
        print(f"   {tampered_line[:60]}...")
        
        # Write tampered log
        with open(audit_log_path, 'w', encoding='utf-8') as f:
            f.writelines(original_lines)
        
        print("✅ Audit log tampered (1 character modified)")
        
        # Step 3: Verify should detect corruption
        print_section("STEP 3: Verify Audit Log (After Tampering)")
        
        print("Running audit-verify...")
        print("Expected: Should detect CORRUPTED")
        
        message, head_hash = verify_audit_log(audit_log_path)
        print(f"Status: {message}")
        
        if "CORRUPTED" in message:
            print("✅ Tampering detected successfully!")
        else:
            print(f"❌ UNEXPECTED: Tampering was not detected!")
            print(f"   Message: {message}")
            # Restore
            shutil.copy(audit_backup, audit_log_path)
            return 1
        
        # Step 4: Restore and test deletion
        print_section("STEP 4: Restore and Test Line Deletion")
        
        print("Restoring original audit log...")
        shutil.copy(audit_backup, audit_log_path)
        
        # Verify it's OK again
        message, _ = verify_audit_log(audit_log_path)
        if "OK" not in message:
            print(f"❌ Unexpected: Restored log is not OK: {message}")
            return 1
        
        print("✅ Audit log restored and verified OK")
        
        # Read again
        with open(audit_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            print("⚠️  Not enough lines to test deletion (need at least 2)")
            print("Skipping deletion test")
        else:
            print(f"\nDeleting line 2 (out of {len(lines)} lines)...")
            
            # Delete second line
            deleted_line = lines[1]
            print(f"Deleted line (first 60 chars):")
            print(f"   {deleted_line[:60]}...")
            
            del lines[1]
            
            # Write modified log
            with open(audit_log_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print(f"✅ Line deleted. New line count: {len(lines)}")
            
            # Step 5: Verify should detect corruption
            print_section("STEP 5: Verify Audit Log (After Deletion)")
            
            print("Running audit-verify...")
            print("Expected: Should detect CORRUPTED (hash chain broken)")
            
            message, head_hash = verify_audit_log(audit_log_path)
            print(f"Status: {message}")
            
            if "CORRUPTED" in message:
                print("✅ Line deletion detected successfully!")
            else:
                print(f"❌ UNEXPECTED: Deletion was not detected!")
                print(f"   Message: {message}")
                # Restore
                shutil.copy(audit_backup, audit_log_path)
                return 1
        
        # Step 6: Restore original
        print_section("STEP 6: Restore Original Audit Log")
        
        print("Restoring original audit log...")
        shutil.copy(audit_backup, audit_log_path)
        os.remove(audit_backup)
        
        message, head_hash = verify_audit_log(audit_log_path)
        print(f"Status: {message}")
        if head_hash:
            print(f"Head hash: {head_hash[:16]}...")
        
        if "OK" in message:
            print("✅ Audit log restored successfully")
        else:
            print(f"⚠️  Warning: Restored log verification: {message}")
        
        # Success
        print_section("DEMO 7 COMPLETE - SUCCESS")
        print(f"✅ Audit log verified OK (before tampering)")
        print(f"✅ Modified 1 character → CORRUPTED detected")
        print(f"✅ Deleted 1 line → CORRUPTED detected")
        print(f"✅ Original audit log restored")
        print("\n🎉 Audit log tampering detection working correctly!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
