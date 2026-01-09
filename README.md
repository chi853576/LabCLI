# LabCLI - Snapshot-based Backup System

Hệ thống backup dựa trên snapshot với các tính năng bảo mật: data integrity verification, anti-rollback, crash consistency, access control, và audit logging.

## 📋 Mục lục

- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
  - [Windows](#windows)
  - [Linux](#linux)
- [Chi tiết kỹ thuật](#chi-tiết-kỹ-thuật)
  - [Chunk Size & Chunking](#chunk-size--chunking)
  - [Canonical Manifest](#canonical-manifest)
  - [Merkle Tree](#merkle-tree)
  - [Anti-Rollback Mechanism](#anti-rollback-mechanism)
  - [Journal/WAL](#journalwal)
  - [Policy & Access Control](#policy--access-control)
  - [Audit Log](#audit-log)
  - [User Identification](#user-identification)
- [CLI commands](#cli-commands)
- [Workflow](#workflow)
- [Hướng dẫn Demo](#hướng-dẫn-demo)

---

## Yêu cầu hệ thống

- **Python**: 3.8 trở lên
- **Dependencies**: PyYAML
- **OS**: Windows, Linux, macOS

---

## Cài đặt


### Windows

```powershell
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Tạo test dataset
python scripts\generate_test_data.py

# 3. Cấu hình policy
# Bước 3.1: Kiểm tra username
echo %USERNAME%
echo %USERDOMAIN%

# Bước 3.2: Mở file policy.yaml và thêm user
# Ví dụ nếu USERNAME=User và USERDOMAIN=DESKTOP-ABC:
# users:
#   DESKTOP-ABC\User: admin

# Bước 3.3: Lưu file policy.yaml

# 4. Khởi tạo backup store
python -m src.cli.main init store\

# 5. Tạo backup đầu tiên
python -m src.cli.main backup dataset\ --label "First backup" --store store\
```

### Linux

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Tạo test dataset
python scripts/generate_test_data.py

# 3. Cấu hình policy
# Bước 3.1: Kiểm tra username
whoami

# Bước 3.2: Mở file policy.yaml và thêm user
# Ví dụ nếu username là alice:
# users:
#   alice: admin

# Bước 3.3: Lưu file policy.yaml

# 4. Khởi tạo backup store
python -m src.cli.main init store/

# 5. Tạo backup đầu tiên
python -m src.cli.main backup dataset/ --label "First backup" --store store/
```

**Chi tiết cấu hình policy.yaml (Linux)**:
```yaml
users:
  # Format: username: role
  alice: admin
  bob: operator
  charlie: auditor
  
roles:
  admin:
    - init
    - backup
    - list-snapshots
    - verify
    - restore
    - audit-verify
  
  operator:
    - backup
    - list-snapshots
    - verify
    - restore
    - audit-verify
  
  auditor:
    - list-snapshots
    - verify
    - audit-verify
```

---

## Chi tiết kỹ thuật

### Chunk Size & Chunking

**Chunk Size**: **1 MiB (1,048,576 bytes)**

**Lý do chọn 1 MiB:**
- **Deduplication hiệu quả**: File thay đổi nhỏ → chỉ backup chunks bị ảnh hưởng
- **Memory footprint thấp**: Chỉ cần 1 MiB RAM khi xử lý mỗi chunk
- **Verify nhanh**: Phát hiện corruption sớm hơn
- **Balance**: Không quá nhỏ (overhead metadata) hay quá lớn (dedup kém)

**Thuật toán Chunking** (`src/core/chunker.py`):
```python
def chunk_file(file_path: str) -> List[bytes]:
    """
    Chia file thành các chunks 1 MiB
    
    Returns:
        List of chunks (mỗi chunk ≤ 1 MiB)
    """
    CHUNK_SIZE = 1024 * 1024  # 1 MiB
    chunks = []
    
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
    
    return chunks
```

**Content-Addressable Storage**:
- Mỗi chunk được hash (SHA-256) → chunk_hash
- Lưu tại: `store/chunks/ab/cd/abcd1234...` (2-level directory)
- Deduplication tự động: cùng nội dung → cùng hash → chỉ lưu 1 lần

---

### Canonical Manifest

**Mục đích**: Đảm bảo manifest có dạng chuẩn (canonical) để tính Merkle root nhất quán

**Format**: JSON với:
- `sort_keys=True`: Sắp xếp keys theo alphabet
- `separators=(',', ':')`: Không có khoảng trắng thừa
- `ensure_ascii=False`: Hỗ trợ Unicode

**Cấu trúc Manifest**:
```json
{
  "files": [
    {
      "chunks": ["hash1", "hash2", "hash3"],
      "path": "dir/file1.txt"
    },
    {
      "chunks": ["hash4", "hash5"],
      "path": "dir/file2.txt"
    }
  ]
}
```

**Thuật toán tạo Canonical Manifest** (`src/core/manifest.py`):
```python
def create_manifest(file_entries: List[FileEntry]) -> dict:
    """
    Tạo canonical manifest từ file entries
    
    Steps:
    1. Sort files theo path (lexicographic order)
    2. Tạo dict với format chuẩn
    3. Serialize với sort_keys=True
    """
    # Sort files by path (canonical order)
    sorted_entries = sorted(file_entries, key=lambda e: e.path)
    
    manifest = {
        "files": [
            {
                "path": entry.path,
                "chunks": entry.chunks
            }
            for entry in sorted_entries
        ]
    }
    
    return manifest

def serialize_manifest(manifest: dict) -> str:
    """Serialize manifest to canonical JSON string"""
    return json.dumps(
        manifest,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    )
```

---

### Merkle Tree

**Mục đích**: Verify data integrity - phát hiện bất kỳ thay đổi nào trong manifest

**Thuật toán** (`src/core/merkle.py`):

```
1. Hash từng file entry:
   file_hash = SHA256(path + ":" + concat(chunk_hashes))

2. Xây dựng Binary Merkle Tree:
   
   Level 0 (leaves):  [H1, H2, H3, H4, ..., Hn]
                       ↓ (nếu lẻ, duplicate cuối)
                      [H1, H2, H3, H4, ..., Hn, Hn]
   
   Level 1:           [H(H1+H2), H(H3+H4), ..., H(H{n-1}+Hn)]
                       ↓ (duplicate nếu lẻ)
   Level 2:           [H(H12+H34),..., H(H{n-3}{n-2}+H{n-1}n)]
                       ↓ (duplicate nếu lẻ)
                      ...
   
   Level m (root):    [H(H1234...{n/2}+H{n/2 +1}{n/2 +2}...n)]
                       ↓
                    Merkle Root

3. Return root hash
```

**Code**:
```python
def compute_merkle_root(manifest: dict) -> str:
    """
    Tính Merkle root từ manifest
    
    Algorithm: Binary Merkle Tree
    """
    # Step 1: Hash each file entry
    file_hashes = [_hash_file_entry(file) for file in manifest["files"]]
    
    if not file_hashes:
        return ""
    
    # Step 2: Build tree bottom-up
    while len(file_hashes) > 1:
        # Duplicate last if odd number
        if len(file_hashes) % 2 != 0:
            file_hashes.append(file_hashes[-1])
        
        # Compute parent level
        new_level = []
        for i in range(0, len(file_hashes), 2):
            combined = file_hashes[i] + file_hashes[i + 1]
            new_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
            new_level.append(new_hash)
        
        file_hashes = new_level
    
    # Step 3: Return root
    return file_hashes[0]

def _hash_file_entry(file_entry: dict) -> str:
    """Hash a single file entry"""
    data = file_entry["path"] + ":" + "".join(file_entry["chunks"])
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
```

**Verification**:
```python
def verify_merkle_root(manifest: dict, expected_root: str) -> bool:
    """Verify manifest integrity"""
    computed_root = compute_merkle_root(manifest)
    return computed_root == expected_root
```

---

### Anti-Rollback Mechanism

**Mục đích**: Ngăn chặn rollback attack (attacker thay snapshot mới bằng snapshot cũ)

**Cơ chế**: Hash chain linking snapshots

```
Snapshot A (t=100):
  merkle_root: "abc123..."
  prev_root: ""  (first snapshot)

Snapshot B (t=200):
  merkle_root: "def456..."
  prev_root: "abc123..."  ← Must match A's merkle_root

Snapshot C (t=300):
  merkle_root: "ghi789..."
  prev_root: "def456..."  ← Must match B's merkle_root
```

**Thuật toán** (`src/core/snapshot.py`):
```python
def load_snapshot(store_path: str, snapshot_id: str, 
                  skip_rollback_check: bool = False) -> SnapshotMetadata:
    """
    Load snapshot và check rollback
    
    Anti-rollback check:
    1. Load snapshot metadata
    2. If has prev_root:
       - List all snapshots
       - Find previous snapshot (by timestamp)
       - Verify: current.prev_root == previous.merkle_root
    3. If mismatch → RollbackDetected exception
    """
```

**Reproduce Rollback Test**:
```bash
# Chạy Demo 4
python demo/demo4_rollback_detection.py

# Hoặc manual:
# 1. Tạo Snapshot A
python -m src.cli.main backup dataset/ --label "Snapshot A" --store store/

# 2. Sửa dataset
echo "new data" > dataset/new_file.txt

# 3. Tạo Snapshot B
python -m src.cli.main backup dataset/ --label "Snapshot B" --store store/

# 4. Simulate rollback attack
# Sửa file store/snapshots/snapshot_B.json:
# Thay merkle_root của B = merkle_root của A

# 5. Verify → Phát hiện rollback
python -m src.cli.main verify snapshot_B --store store/
# Output: Rollback detected!
```

---

### Journal/WAL

**Mục đích**: Crash consistency - đảm bảo store không bị corrupt khi crash giữa chừng backup

**Cơ chế**: Write-Ahead Log (WAL) với atomic transactions

**Format Journal** (`store/journal.wal`):
```
BEGIN txn_1234567890 backup
WRITE txn_1234567890 {"snapshot_id": "snapshot_123", "label": "Test"}
COMMIT txn_1234567890
```

**Transaction Flow**:
```
1. BEGIN transaction
   → Write "BEGIN txn_id operation" to journal

2. Perform operations (create snapshot, etc.)
   → Write "WRITE txn_id data" to journal

3. COMMIT transaction
   → Write "COMMIT txn_id" to journal
   → Fsync journal file
   → Clear journal

If crash before COMMIT:
   → On recovery: Rollback uncommitted transactions
   → Delete incomplete snapshot files
```

**Code** (`src/core/journal.py`):


**Reproduce Crash Test**:
```bash
# Chạy Demo 5
python demo/demo5_crash_consistency.py

# Hoặc manual:
# 1. Tạo baseline backup
python -m src.cli.main backup dataset/ --label "Baseline" --store store/

# 2. Simulate crash during backup
python scripts/crash_simulation.py dataset/ store/ 2.0
# → Kills backup process after 2 seconds

# 3. Check store
python -m src.cli.main list-snapshots --store store/
# → Incomplete snapshot NOT in list (rolled back)

# 4. Backup again
python -m src.cli.main backup dataset/ --label "After recovery" --store store/
# → Success! Store still functional
```

---

### Policy & Access Control

**File**: `policy.yaml`

**Schema**:
```yaml
# Users mapping: OS username → role
users:
  <os_username>: <role_name>

# Roles mapping: role → list of allowed commands
roles:
  <role_name>:
    - <command1>
    - <command2>
```

**Ví dụ**:
```yaml
users:
  # Windows users (DOMAIN\Username format)
  DESKTOP-ABC\Alice: admin
  DESKTOP-ABC\Bob: operator
  
  # Linux/macOS users (username only)
  alice: admin
  bob: operator
  charlie: auditor

roles:
  # Admin: full access
  admin:
    - init
    - backup
    - list-snapshots
    - verify
    - restore
    - audit-verify
  
  # Operator: can backup and restore
  operator:
    - backup
    - list-snapshots
    - verify
    - restore
    - audit-verify
  
  # Auditor: read-only access
  auditor:
    - list-snapshots
    - verify
    - audit-verify
```

**Enforcement** (`src/security/policy.py`):
```python
def check_permission(command: str) -> bool:
    """
    Check if current user can run command
    
    Steps:
    1. Get current OS user
    2. Load policy.yaml
    3. Find user's role
    4. Check if command in role's allowed commands
    """
    policy = load_policy()
    user = get_current_user()
    role = policy['users'].get(user)
    
    if not role:
        return False  # User not in policy
    
    allowed_commands = policy['roles'].get(role, [])
    return command in allowed_commands
```

**Test**:
```bash
# Chạy Demo 6
python demo/demo6_policy_deny.py

# Hoặc manual:
# 1. Đổi role thành auditor trong policy.yaml
# 2. Thử chạy lệnh init
python -m src.cli.main init store/
# → Permission denied!

# 3. Check audit log
cat store/audit.log
# → Có entry với status DENY
```

---

### Audit Log

**File**: `store/audit.log`

**Mục đích**: Tamper-proof audit trail với hash chain

**Format mỗi dòng**:
```
ENTRY_HASH PREV_HASH UNIX_MS USER COMMAND ARGS_SHA256 STATUS
```

**Ví dụ**:
```
7006cfe1a0079bdd... 0000000000000000... 1767941758000 alice init d41d8cd98f00b204... OK
a1b2c3d4e5f6g7h8... 7006cfe1a0079bdd... 1767941759000 alice backup 5d41402abc4b2a76... OK
9876543210fedcba... a1b2c3d4e5f6g7h8... 1767941760000 bob restore 7d793037a0760186... DENY
```

**Cách tính Hash**:
```python
def log_audit(command: str, args: list[str], status: str, log_path: str):
    """
    Ghi audit entry với hash chain
    
    Hash calculation:
    1. ARGS_SHA256 = SHA256(join(args, " "))
    2. PREV_HASH = ENTRY_HASH của dòng trước (hoặc "0"*64 nếu dòng đầu)
    3. CONTENT = f"{PREV_HASH} {UNIX_MS} {USER} {COMMAND} {ARGS_SHA256} {STATUS}"
    4. ENTRY_HASH = SHA256(CONTENT)
    5. LOG_LINE = f"{ENTRY_HASH} {CONTENT}\n"
    """

```

**Verification**:
```python
def verify_audit_log(log_path: str) -> tuple[str, str | None]:
    """
    Verify audit log integrity
    
    Steps:
    1. Read all lines
    2. For each line:
       - Parse: entry_hash, prev_hash, ...
       - Check: prev_hash == previous line's entry_hash
       - Recompute: entry_hash from content
       - Verify: computed == stored
    3. Return: ("AUDIT OK", head_hash) or ("AUDIT CORRUPTED: ...", None)
    """
```

**Chạy audit-verify**:
```bash
# Verify audit log
python -m src.cli.main audit-verify --store store/

# Output nếu OK:
# AUDIT OK
# Head hash: a1b2c3d4e5f6g7h8...

# Output nếu corrupted:
# AUDIT CORRUPTED: Entry hash mismatch at line 5
```

**Test tampering**:
```bash
# Chạy Demo 7
python demo/demo7_audit_tampering.py

# Hoặc manual:
# 1. Sửa 1 ký tự trong audit.log
# 2. Chạy verify
python -m src.cli.main audit-verify --store store/
# → AUDIT CORRUPTED detected!
```

---

### User Identification

**Mục đích**: Xác định OS user để enforce policy và ghi audit log

**Thuật toán** (`src/security/user.py`):
```python
def get_current_user() -> str:
    """
    Xác định OS user
    
    Priority:
    1. SUDO_USER (nếu có) - Linux/macOS khi dùng sudo
    2. Platform-specific:
       - Linux/macOS: os.getlogin() → $USER → $LOGNAME
       - Windows: $USERNAME + $USERDOMAIN → "DOMAIN\Username"
    3. Raise ValueError nếu không xác định được
    """
```

**Ví dụ**:
```bash
# Linux
$ whoami
alice
$ python -c "from src.security.user import get_current_user; print(get_current_user())"
alice

# Linux with sudo
$ sudo python -c "from src.security.user import get_current_user; print(get_current_user())"
alice  # Returns SUDO_USER, not root

# Windows
C:\> echo %USERNAME%
Alice
C:\> python -c "from src.security.user import get_current_user; print(get_current_user())"
DESKTOP-ABC\Alice
```

---

## CLI Commands

```bash
# Initialize backup store
python -m src.cli.main init <store_path>

# Create backup
python -m src.cli.main backup <source_path> --label <label> --store <store_path>

# List snapshots
python -m src.cli.main list-snapshots --store <store_path>

# Verify snapshot
python -m src.cli.main verify <snapshot_id> --store <store_path>

# Restore snapshot
python -m src.cli.main restore <snapshot_id> <target_path> --store <store_path>

# Verify audit log
python -m src.cli.main audit-verify --store <store_path>
```

## Workflow

```bash
# 1. Init
python -m src.cli.main init store/

# 2. Backup
python -m src.cli.main backup dataset/ --label "First backup" --store store/

# 3. List
python -m src.cli.main list-snapshots --store store/

# 4. Verify
python -m src.cli.main verify snapshot_1234567890 --store store/

# 5. Restore
python -m src.cli.main restore snapshot_1234567890 restored/ --store store/

# 6. Audit
python -m src.cli.main audit-verify --store store/
```

---



## Hướng dẫn Demo


Trước khi chạy demo, đảm bảo:
1. Dataset đã được tạo: `python scripts/generate_test_data.py`
2. Store đã được khởi tạo: `python -m src.cli.main init store/`
3. **Username đã được thêm vào `policy.yaml`** (xem hướng dẫn bên dưới)

### Cấu hình Policy

#### Windows
```powershell
# Kiểm tra username
echo %USERNAME%
echo %USERDOMAIN%

# Mở policy.yaml và thêm:
# users:
#   DESKTOP-ABC\YourUsername: admin
```

#### Linux/macOS
```bash
# Kiểm tra username
whoami

# Mở policy.yaml và thêm:
# users:
#   your_username: admin
```

**Ví dụ policy.yaml**:
```yaml
users:
  # Windows
  DESKTOP-ABC\Alice: admin
  
  # Linux/macOS
  bob: admin

roles:
  admin:
    - init
    - backup
    - list-snapshots
    - verify
    - restore
    - audit-verify
```


### Lưu ý quan trọng

**Luôn reset store trước khi chạy demo mới** để tránh lỗi do dữ liệu cũ, lệnh reset:

#### Windows (PowerShell)
```powershell
Remove-Item -Path store -Recurse -Force
python -m src.cli.main init store\
```

#### Linux/macOS
```bash
rm -rf store/
python -m src.cli.main init store/
```

---

### Demo 1: Restore Integrity

**Mục đích**: Kiểm tra tính toàn vẹn khi restore dữ liệu

#### Windows
```powershell
# Reset store
Remove-Item -Path store -Recurse -Force
python -m src.cli.main init store\

# Chạy demo
python demo\demo1_restore_integrity.py
```

#### Linux/macOS
```bash
# Reset store
rm -rf store/
python -m src.cli.main init store/

# Chạy demo
python demo/demo1_restore_integrity.py
```

---

### Demo 2: Chunk Corruption Detection

**Mục đích**: Phát hiện chunk bị sửa đổi

#### Windows
```powershell
# Reset store
Remove-Item -Path store -Recurse -Force
python -m src.cli.main init store\

# Chạy demo
python demo\demo2_chunk_corruption.py
```

#### Linux/macOS
```bash
# Reset store
rm -rf store/
python -m src.cli.main init store/

# Chạy demo
python demo/demo2_chunk_corruption.py
```

---

### Demo 3: Manifest Corruption Detection

**Mục đích**: Phát hiện manifest bị sửa đổi

#### Windows
```powershell
# Reset store
Remove-Item -Path store -Recurse -Force
python -m src.cli.main init store\

# Chạy demo
python demo\demo3_manifest_corruption.py
```

#### Linux/macOS
```bash
# Reset store
rm -rf store/
python -m src.cli.main init store/

# Chạy demo
python demo/demo3_manifest_corruption.py
```

---

### Demo 4: Rollback Attack Detection

**Mục đích**: Phát hiện rollback attack

#### Windows
```powershell
# Reset store
Remove-Item -Path store -Recurse -Force
python -m src.cli.main init store\

# Chạy demo
python demo\demo4_rollback_detection.py
```

#### Linux/macOS
```bash
# Reset store
rm -rf store/
python -m src.cli.main init store/

# Chạy demo
python demo/demo4_rollback_detection.py
```

---

### Demo 5: Crash Consistency

**Mục đích**: Kiểm tra khả năng phục hồi sau crash

#### Windows
```powershell
# Reset store
Remove-Item -Path store -Recurse -Force
python -m src.cli.main init store\

# Chạy demo
python demo\demo5_crash_consistency.py
```

#### Linux/macOS
```bash
# Reset store
rm -rf store/
python -m src.cli.main init store/

# Chạy demo
python demo/demo5_crash_consistency.py
```

---

### Demo 6: Policy Enforcement

**Mục đích**: Kiểm tra phân quyền theo role

#### Windows
```powershell
# Reset store
Remove-Item -Path store -Recurse -Force
python -m src.cli.main init store\

# Chạy demo
python demo\demo6_policy_deny.py
```

#### Linux/macOS
```bash
# Reset store
rm -rf store/
python -m src.cli.main init store/

# Chạy demo
python demo/demo6_policy_deny.py
```

**Lưu ý**: Demo này sẽ tạm thời sửa `policy.yaml` và tự động khôi phục.

---

### Demo 7: Audit Log Tampering Detection

**Mục đích**: Phát hiện audit log bị sửa đổi

#### Windows
```powershell
# Reset store (cần có audit log trước)
Remove-Item -Path store -Recurse -Force
python -m src.cli.main init store\
python -m src.cli.main backup dataset\ --label "Test" --store store\

# Chạy demo
python demo\demo7_audit_tampering.py
```

#### Linux/macOS
```bash
# Reset store (cần có audit log trước)
rm -rf store/
python -m src.cli.main init store/
python -m src.cli.main backup dataset/ --label "Test" --store store/

# Chạy demo
python demo/demo7_audit_tampering.py
```
