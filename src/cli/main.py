"""
CLI main entry point - MEMBER 3

Nhiệm vụ:
- Argument parsing (argparse)
- Route đến commands.py
- 6 lệnh: init, backup, list-snapshots, verify, restore, audit-verify

Tham khảo: src/interfaces.py
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import commands


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="LabCLI - Snapshot-based backup system with integrity verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize backup store
  python -m src.cli.main init store/
  
  # Create backup
  python -m src.cli.main backup dataset/ --label "First backup" --store store/
  
  # List snapshots
  python -m src.cli.main list-snapshots --store store/
  
  # Verify snapshot
  python -m src.cli.main verify snapshot_1234567890 --store store/
  
  # Restore snapshot
  python -m src.cli.main restore snapshot_1234567890 output/ --store store/
  
  # Verify audit log
  python -m src.cli.main audit-verify --store store/
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # ========== init ==========
    parser_init = subparsers.add_parser(
        "init",
        help="Initialize backup store"
    )
    parser_init.add_argument(
        "store_path",
        help="Path to backup store directory"
    )
    
    # ========== backup ==========
    parser_backup = subparsers.add_parser(
        "backup",
        help="Create a backup snapshot"
    )
    parser_backup.add_argument(
        "source_path",
        help="Path to source directory to backup"
    )
    parser_backup.add_argument(
        "--label",
        required=True,
        help="Snapshot label (required)"
    )
    parser_backup.add_argument(
        "--store",
        default="store",
        help="Backup store path (default: store)"
    )
    
    # ========== list-snapshots ==========
    parser_list = subparsers.add_parser(
        "list-snapshots",
        help="List all snapshots"
    )
    parser_list.add_argument(
        "--store",
        default="store",
        help="Backup store path (default: store)"
    )
    
    # ========== verify ==========
    parser_verify = subparsers.add_parser(
        "verify",
        help="Verify a snapshot's integrity"
    )
    parser_verify.add_argument(
        "snapshot_id",
        help="Snapshot ID to verify"
    )
    parser_verify.add_argument(
        "--store",
        default="store",
        help="Backup store path (default: store)"
    )
    
    # ========== restore ==========
    parser_restore = subparsers.add_parser(
        "restore",
        help="Restore a snapshot to target directory"
    )
    parser_restore.add_argument(
        "snapshot_id",
        help="Snapshot ID to restore"
    )
    parser_restore.add_argument(
        "target_path",
        help="Target directory for restore"
    )
    parser_restore.add_argument(
        "--store",
        default="store",
        help="Backup store path (default: store)"
    )
    
    # ========== audit-verify ==========
    parser_audit = subparsers.add_parser(
        "audit-verify",
        help="Verify audit log integrity"
    )
    parser_audit.add_argument(
        "--store",
        default="store",
        help="Backup store path (default: store)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command specified, print help
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        # Route to appropriate command
        if args.command == "init":
            commands.cmd_init(args.store_path)
        
        elif args.command == "backup":
            commands.cmd_backup(args.store, args.source_path, args.label)
        
        elif args.command == "list-snapshots":
            commands.cmd_list_snapshots(args.store)
        
        elif args.command == "verify":
            commands.cmd_verify(args.store, args.snapshot_id)
        
        elif args.command == "restore":
            commands.cmd_restore(args.store, args.snapshot_id, args.target_path)
        
        elif args.command == "audit-verify":
            commands.cmd_audit_verify(args.store)
        
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            sys.exit(1)
    
    except PermissionError as e:
        print(f"\n❌ Permission denied: {e}")
        print("Hint: Check policy.yaml to ensure your user has the required role.")
        sys.exit(1)
    
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
