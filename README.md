# yêu cầu

- Python 3.8+
- PyYAML
- pytest (for testing)

### 1. Clone repository

```bash
git clone https://github.com/chi853576/LabCLI.git
cd LabCLI
```

### 2. cài dependencies

```bash
# Cài dependencies
pip install PyYAML pytest
# Hoặc dùng requirements.txt
pip install -r requirements.txt
```

### 3. Tạo test dataset (local only, không commit vào Git)

Mục đích: tạo dữ liệu dataset ngẫu nhiên để test

```bash
# Chạy script tạo test data
python scripts/generate_test_data.py

# Hoặc tự tạo:
mkdir dataset
# Copy files vào dataset/
```


### 4. Cấu hình policy (Chỉ cần khi test CLI - sau khi code xong)

**Lưu ý:** Bước này KHÔNG CẦN khi đang code. Chỉ cần khi Member 3 đã integrate CLI xong và muốn test commands.

**Bước 1: Kiểm tra username**

```bash
# Windows
echo %USERNAME%

# Linux/macOS
whoami
```

**Bước 2: Mở file `policy.yaml` và thêm username của bạn**

```yaml
users:
  # Thêm dòng này (thay YOUR_USERNAME bằng username thực tế)
  YOUR_USERNAME: admin
  
  # Ví dụ:
  # DELL: admin        # Windows user
  # alice: admin       # Linux user
```

**Bước 3: Test CLI (sau khi Member 3 implement xong)**

```bash
# Chạy thử lệnh
python -m src.cli.main list-snapshots

# Nếu thành công: hiện danh sách snapshots
# Nếu lỗi: Permission denied!
```


## Cấu trúc thư mục

```
LabCLI/
├── src/
│   ├── interfaces.py       # Interface contracts (ĐỌC ĐẦU TIÊN!)
│   ├── core/               # Core backup logic (Member 1, 2, 3)
│   │   ├── chunker.py      # File chunking (Member 1)
│   │   ├── storage.py      # Content-addressable storage (Member 1)
│   │   ├── manifest.py     # Manifest generation (Member 2)
│   │   ├── merkle.py       # Merkle tree (Member 2)
│   │   ├── snapshot.py     # Snapshot management (Member 2)
│   │   └── journal.py      # WAL/Journal (Member 3)
│   ├── security/           # Security features (Member 4)
│   │   ├── user.py         # User identification
│   │   ├── policy.py       # Policy enforcement
│   │   └── audit.py        # Audit logging
│   ├── cli/                # CLI interface (Member 3)
│   │   ├── commands.py     # Command implementations
│   │   └── main.py         # Entry point
│   └── utils/              # Utilities (shared)
│       └── hash.py         # Hashing utilities
├── tests/                  # Tests
│   ├── test_core/          # Unit tests for core
│   ├── test_security/      # Unit tests for security
│   └── test_integration/   # Integration tests
├── dataset/                # Test dataset (NOT in Git)
├── store/                  # Backup store (NOT in Git, generated)
├── policy.yaml             # Policy configuration
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Interfaces (src/interfaces.py)

File `interfaces.py` định nghĩa tất cả function signatures và data structures, đã phân thành các function cho từng thành viên. Cần đọc đầu tiên trước khi làm việc

## Các quyết định thiết kế

### Chunk size: 1 MiB (1,048,576 bytes)
**Lý do:**
- Deduplication hiệu quả (file thay đổi nhỏ → chỉ backup chunks bị ảnh hưởng)
- Memory footprint thấp (chỉ cần 1 MiB RAM khi xử lý mỗi chunk)
- Verify nhanh hơn khi phát hiện lỗi

### Manifest: JSON
**Lý do:**
- Deterministic encoding (sort_keys=True, separators=(',', ':'))
- Phù hợp cho Merkle tree (cần hash nhất quán)

### Policy: YAML
**Lý do:**
- Dễ đọc và chỉnh sửa thủ công
- Hỗ trợ comments
- Phù hợp cho config file

### Hash algorithm: SHA-256
**Lý do:**
- thầy yêu cầu