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

## 🔐 Thuật toán xây dựng Merkle Tree
### Tổng quan
Mỗi snapshot được gắn với một Merkle root, là một giá trị hash của toàn bộ nội dung của snapshot. Cụ thể, ở hàm
```python
def compute_merkle_root(manifest: dict) -> str:
```
Ta thấy `manifest` chứa toàn bộ cấu trúc của snapshot. Khi truyền vào hàm `compute_merkle_root` thì `manifest` này sẽ được băm (hash) lại thành một chuỗi dạng string duy nhất.

### Chi tiết thuật toán
- Đầu tiên, mỗi file trong `manifest` sẽ được băm thông qua hàm `_hash_file_entry(file)`. Cụ thể, việc băm sẽ thực hiện thông qua chương trình sau:
```python
def _hash_file_entry(file_entry: dict) -> str:
    data = file_entry["path"] + ":" + "".join(file_entry["chunks"])
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
```
Tại đây, chuỗi `data` sẽ bao gồm đường dẫn của tệp tin `file_entry["path"]`, theo sau đó là dấu ":", và cuối cùng là các chunk của tệp tin. Sau đó, chuỗi `data` này sẽ được băm bởi thuật toán `sha256` và hàm sẽ trả về giá trị là chính kết quả băm đó.
- Sau khi thực hiện quá trình băm các file, các giá trị này sẽ được đưa vào mảng `file_hashes` như sau: 
```python
file_hashes = [_hash_file_entry(file) for file in manifest["files"]]
```
Đây chính là các node lá trong Merkle tree, chứa các giá trị đã băm của các file. Hay nói cách khác, mỗi phần tử trong `file_hashses` chính là một node lá. Dĩ nhiên, thứ tự của các chuỗi hash của các file này đã được đảm bảo tính canonical trước đó ở trong hàm:
```python
def create_manifest(file_entries: List[FileEntry]) -> dict:
```
- Tiếp theo, chương trình sẽ tiến hành tạo lần lượt các node có độ sâu thấp hơn so với các node lá, cho tới khi tạo được node gốc thông qua vòng lặp:
```python
while len(file_hashes) > 1:
  if len(file_hashes) % 2 != 0:
      file_hashes.append(file_hashes[-1])
  
  new_level = []
  for i in range(0, len(file_hashes), 2):
      combined = file_hashes[i] + file_hashes[i + 1]
      new_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
      new_level.append(new_hash)
  
  file_hashes = new_level
```
Bởi vì trong quá trình lặp, có thể số node hiện hành (hay số phần tử của `file_hashes`) không phải là số chẵn, khiến cho Merkle tree không đảm bảo tính chất của một cây nhị phân. Nếu trường hợp đó xảy ra, ta sẽ tiến hành nhân đôi thêm node cuối, hay bổ sung thêm một phần tử có giá trị bằng với giá trị của phần tử cuối cùng trong mảng `file_hashes` vào trong mảng `file_hashes`
```python
if len(file_hashes) % 2 != 0:
  file_hashes.append(file_hashes[-1])
```
- Tiếp theo, hệ thống sẽ tạo các node cha, thông qua việc ghép lần lượt 2 node con kề nhau và băm chúng bằng thuật toán SHA256 và tạm thời lưu chúng vào mảng `new_level`. Tới khi việc tạo các node cha hoàn tất thì gán `file_hashes` bằng `new_level`.
```python
new_level = []
for i in range(0, len(file_hashes), 2):
    combined = file_hashes[i] + file_hashes[i + 1]
    new_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    new_level.append(new_hash)

file_hashes = new_level
```
- Quá trình tạo các node có mức thấp hơn này sẽ kết thúc khi mảng `file_hashes` chỉ còn lại đúng 1 phần tử, đó cũng chính là node gốc (Root node) của Merkel Tree.
```python
while len(file_hashes) > 1:
```