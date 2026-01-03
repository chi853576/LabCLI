from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


# ============= CẤU TRÚC DỮ LIỆU =============

@dataclass
class ChunkInfo:
    """Thông tin về 1 chunk"""
    hash: str          # SHA-256 hash (64 ký tự hex)
    size: int          # Kích thước tính bằng bytes


@dataclass
class FileEntry:
    """Entry trong manifest - đại diện cho 1 file"""
    path: str          # Đường dẫn tương đối từ source root
    chunks: List[str]  # Danh sách chunk hashes theo thứ tự (từ đầu đến cuối file)


@dataclass
class SnapshotMetadata:
    """Metadata của snapshot"""
    id: str            # Format: snapshot_TIMESTAMP
    label: str         # Nhãn do người dùng cung cấp
    timestamp: int     # Unix timestamp (giây)
    merkle_root: str   # Merkle root hash
    prev_root: str     # Merkle root của snapshot trước (cho anti-rollback, rỗng nếu là snapshot đầu tiên)
    manifest_hash: str # SHA-256 hash của manifest


# ============= MEMBER 1: STORAGE & CHUNKING =============

def init_storage(store_path: str) -> None:
    """
    Khởi tạo cấu trúc thư mục storage.
    Tạo: store_path/chunks/ directory
    
    Args:
        store_path: Đường dẫn đến backup store
    """
    pass


def chunk_file(file_path: str, chunk_size: int = 1*1024*1024) -> List[bytes]:
    """
    Chia file thành các chunks có kích thước cố định.
    
    Args:
        file_path: Đường dẫn đến file cần chia
        chunk_size: Kích thước mỗi chunk tính bằng bytes (mặc định 1 MiB = 1,048,576 bytes)
    
    Returns:
        Danh sách dữ liệu chunk (bytes)
    """
    pass


def hash_chunk(chunk_data: bytes) -> str:
    """
    Tính SHA-256 hash của chunk.
    
    Args:
        chunk_data: Dữ liệu chunk dạng bytes
    
    Returns:
        SHA-256 hash dạng chuỗi hex (64 ký tự)
    """
    pass


def store_chunk(store_path: str, chunk_data: bytes) -> str:
    """
    Lưu chunk vào content-addressable storage.
    Đường dẫn lưu: store_path/chunks/XX/XXXXXX... (2 ký tự đầu của hash làm thư mục con)
    
    Deduplication: Nếu chunk với cùng hash đã tồn tại, không ghi lại.
    
    Args:
        store_path: Đường dẫn đến backup store
        chunk_data: Dữ liệu chunk cần lưu
    
    Returns:
        SHA-256 hash của chunk
    """
    pass


def get_chunk(store_path: str, chunk_hash: str) -> bytes:
    """
    Lấy dữ liệu chunk theo hash.
    
    Args:
        store_path: Đường dẫn đến backup store
        chunk_hash: SHA-256 hash của chunk
    
    Returns:
        Dữ liệu chunk dạng bytes
    
    Raises:
        FileNotFoundError: Nếu chunk không tồn tại
    """
    pass


def chunk_exists(store_path: str, chunk_hash: str) -> bool:
    """
    Kiểm tra chunk có tồn tại trong storage không.
    
    Args:
        store_path: Đường dẫn đến backup store
        chunk_hash: SHA-256 hash của chunk
    
    Returns:
        True nếu chunk tồn tại, False nếu không
    """
    pass


# ============= MEMBER 2: MANIFEST & MERKLE =============

def create_manifest(file_entries: List[FileEntry]) -> dict:
    """
    Tạo canonical manifest từ danh sách file entries.
    
    Yêu cầu canonical format:
    - Files được sắp xếp theo path (tăng dần)
    - Với mỗi file, chunks theo đúng thứ tự từ đầu đến cuối file
    - JSON encoding phải deterministic
    
    Args:
        file_entries: Danh sách các FileEntry objects
    
    Returns:
        Canonical manifest dạng dict
    """
    pass


def serialize_manifest(manifest: dict) -> str:
    """
    Serialize manifest thành chuỗi JSON canonical.
    Phải deterministic (cùng input → cùng output).
    
    Args:
        manifest: Manifest dict
    
    Returns:
        Chuỗi JSON (keys đã sắp xếp, không có khoảng trắng thừa)
    """
    pass


def hash_manifest(manifest: dict) -> str:
    """
    Tính SHA-256 hash của canonical manifest.
    
    Args:
        manifest: Manifest dict
    
    Returns:
        SHA-256 hash của serialized manifest
    """
    pass


def compute_merkle_root(manifest: dict) -> str:
    """
    Tính Merkle root từ manifest.
    
    Thuật toán: Binary Merkle tree trên các file entries đã sắp xếp.
    Phải document thuật toán chi tiết trong README.
    
    Args:
        manifest: Canonical manifest
    
    Returns:
        Merkle root hash (SHA-256)
    """
    pass


def verify_merkle_root(manifest: dict, expected_root: str) -> bool:
    """
    Xác minh Merkle root của manifest.
    
    Args:
        manifest: Manifest cần xác minh
        expected_root: Merkle root mong đợi
    
    Returns:
        True nếu khớp, False nếu không
    """
    pass


def create_snapshot(store_path: str, manifest: dict, label: str, prev_root: str = "") -> str:
    """
    Tạo snapshot metadata và lưu vào store.
    
    Lưu vào: store_path/snapshots/snapshot_TIMESTAMP.json
    
    Args:
        store_path: Đường dẫn đến backup store
        manifest: Manifest dict
        label: Nhãn do người dùng cung cấp
        prev_root: Merkle root của snapshot trước (rỗng nếu là snapshot đầu tiên)
    
    Returns:
        snapshot_id (ví dụ: "snapshot_1234567890")
    """
    pass


def load_snapshot(store_path: str, snapshot_id: str) -> SnapshotMetadata:
    """
    Load snapshot metadata từ store.
    
    Args:
        store_path: Đường dẫn đến backup store
        snapshot_id: Snapshot ID
    
    Returns:
        SnapshotMetadata object
    
    Raises:
        FileNotFoundError: Nếu snapshot không tồn tại
    """
    pass


def list_snapshots(store_path: str) -> List[SnapshotMetadata]:
    """
    Liệt kê tất cả snapshots, sắp xếp theo timestamp (cũ nhất trước).
    
    Args:
        store_path: Đường dẫn đến backup store
    
    Returns:
        Danh sách SnapshotMetadata objects
    """
    pass


def get_latest_snapshot(store_path: str) -> Optional[SnapshotMetadata]:
    """
    Lấy snapshot mới nhất (để lấy prev_root).
    
    Args:
        store_path: Đường dẫn đến backup store
    
    Returns:
        SnapshotMetadata mới nhất hoặc None nếu không có snapshot nào
    """
    pass


def load_manifest(store_path: str, manifest_hash: str) -> dict:
    """
    Load manifest theo hash.
    
    Args:
        store_path: Đường dẫn đến backup store
        manifest_hash: SHA-256 hash của manifest
    
    Returns:
        Manifest dict
    
    Raises:
        FileNotFoundError: Nếu manifest không tồn tại
    """
    pass


# ============= MEMBER 3: JOURNAL/WAL =============

def init_journal(store_path: str) -> None:
    """
    Khởi tạo journal/WAL file.
    Tạo: store_path/journal.wal
    
    Args:
        store_path: Đường dẫn đến backup store
    """
    pass


def journal_begin(store_path: str, operation: str) -> str:
    """
    Bắt đầu một transaction.
    Ghi: BEGIN <txn_id> <operation> <timestamp>
    
    Args:
        store_path: Đường dẫn đến backup store
        operation: Tên operation (ví dụ: "backup")
    
    Returns:
        Transaction ID (unique)
    """
    pass


def journal_write(store_path: str, txn_id: str, record: dict) -> None:
    """
    Ghi một record vào journal.
    Ghi: WRITE <txn_id> <record_json>
    
    Args:
        store_path: Đường dẫn đến backup store
        txn_id: Transaction ID
        record: Dữ liệu record dạng dict
    """
    pass


def journal_commit(store_path: str, txn_id: str) -> None:
    """
    Commit một transaction.
    Ghi: COMMIT <txn_id> <timestamp>
    
    Args:
        store_path: Đường dẫn đến backup store
        txn_id: Transaction ID
    """
    pass


def journal_recover(store_path: str) -> None:
    """
    Khôi phục sau crash bằng cách xử lý journal.
    
    - Đọc journal.wal
    - Với mỗi uncommitted transaction: rollback (xóa snapshot chưa hoàn thành)
    - Dọn dẹp journal
    
    Args:
        store_path: Đường dẫn đến backup store
    """
    pass


# ============= MEMBER 4: SECURITY (POLICY & AUDIT) =============

def get_current_user() -> str:
    """
    Lấy OS user hiện tại để xác thực.
    
    Ưu tiên:
    1. Nếu có SUDO_USER env → trả về SUDO_USER (người dùng thực gọi sudo)
    2. Nếu không → trả về OS username
    
    Format:
    - Linux/macOS: username (ví dụ: "alice")
    - Windows: DOMAIN\\Username hoặc Username (ví dụ: "ACME\\bob" hoặc "bob")
    
    Returns:
        Chuỗi username
    
    Raises:
        RuntimeError: Nếu không thể xác định username
    """
    pass


def load_policy(policy_path: str) -> dict:
    """
    Load và parse policy.yaml.
    
    Args:
        policy_path: Đường dẫn đến policy.yaml
    
    Returns:
        Policy dict với keys: "users", "roles"
    
    Raises:
        FileNotFoundError: Nếu policy file không tồn tại
        yaml.YAMLError: Nếu policy file không hợp lệ
    """
    pass


def check_permission(policy: dict, user: str, command: str) -> bool:
    """
    Kiểm tra user có quyền chạy command không.
    
    Logic:
    1. Tra cứu role của user trong policy["users"]
    2. Kiểm tra command có trong policy["roles"][role] không
    
    Args:
        policy: Policy dict từ load_policy()
        user: Username
        command: Tên command (ví dụ: "backup", "restore")
    
    Returns:
        True nếu được phép, False nếu không
    """
    pass


def init_audit_log(store_path: str) -> None:
    """
    Khởi tạo audit log file.
    Tạo: store_path/audit.log (rỗng hoặc có header)
    
    Args:
        store_path: Đường dẫn đến backup store
    """
    pass


def log_audit(store_path: str, user: str, command: str, args: List[str], status: str) -> None:
    """
    Thêm audit entry vào log với hash chain.
    
    Format: ENTRY_HASH PREV_HASH UNIX_MS USER COMMAND ARGS_SHA256 STATUS
    
    Trong đó:
    - ENTRY_HASH = SHA256(PREV_HASH + UNIX_MS + USER + COMMAND + ARGS_SHA256 + STATUS)
    - PREV_HASH = ENTRY_HASH của dòng trước (hoặc "0" cho entry đầu tiên)
    - UNIX_MS = Unix timestamp tính bằng milliseconds
    - USER = Username từ get_current_user()
    - COMMAND = Tên command
    - ARGS_SHA256 = SHA256 của " ".join(args)
    - STATUS = "OK" | "DENY" | "FAIL"
    
    Args:
        store_path: Đường dẫn đến backup store
        user: Username
        command: Tên command
        args: Arguments của command (danh sách strings)
        status: Trạng thái ("OK", "DENY", hoặc "FAIL")
    """
    pass


def verify_audit_log(store_path: str) -> Tuple[bool, str]:
    """
    Xác minh tính toàn vẹn hash chain của audit log.
    
    Kiểm tra:
    1. Tính lại ENTRY_HASH cho mỗi dòng
    2. Xác minh chuỗi PREV_HASH liên tục
    
    Args:
        store_path: Đường dẫn đến backup store
    
    Returns:
        (is_valid, message)
        - is_valid: True nếu hợp lệ, False nếu bị hỏng
        - message: "AUDIT OK" hoặc chi tiết lỗi
    """
    pass


# ============= HELPER FUNCTIONS (Shared) =============

def compute_sha256(data: bytes) -> str:
    """
    Tính SHA-256 hash của dữ liệu.
    
    Args:
        data: Dữ liệu cần hash
    
    Returns:
        SHA-256 hash dạng chuỗi hex (64 ký tự)
    """
    pass


def scan_directory(path: str) -> List[str]:
    """
    Quét thư mục đệ quy và trả về danh sách đường dẫn file.
    
    Args:
        path: Đường dẫn thư mục cần quét
    
    Returns:
        Danh sách đường dẫn file tuyệt đối (không bao gồm thư mục)
    """
    pass
