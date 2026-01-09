"""
Snapshot management module - MEMBER 2

Nhiệm vụ:
- Tạo và lưu snapshot metadata (id, label, timestamp, merkle_root, prev_root, manifest_hash)
- Load snapshot từ store
- List snapshots, get latest snapshot
- Load manifest theo hash

Tham khảo: src/interfaces.py
"""

# TODO: Implement create_snapshot(), load_snapshot(), list_snapshots(), get_latest_snapshot(), load_manifest()
from typing import List, Dict, Tuple, Optional
import time
import os
from src.interfaces import SnapshotMetadata
import json
class RollbackDetected(Exception):
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
    timestamp = int(time.time())
    snapshot_id = f"snapshot_{timestamp}"
    
    from src.core.merkle import compute_merkle_root
    from src.core.manifest import hash_manifest

    merkle_root = compute_merkle_root(manifest)
    manifest_hash = hash_manifest(manifest)
    
    snapshot_metadata = {
        "id": snapshot_id,
        "label": label,
        "timestamp": timestamp,
        "merkle_root": merkle_root,
        "prev_root": prev_root,
        "manifest_hash": manifest_hash
    }
    
    snapshots_dir = os.path.join(store_path, "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)
    
    snapshot_path = os.path.join(snapshots_dir, f"{snapshot_id}.json")
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_metadata, f, ensure_ascii=False, indent=4)
    
    return snapshot_id


def load_snapshot(store_path: str, snapshot_id: str, skip_rollback_check: bool = False) -> SnapshotMetadata:
    """
    Load snapshot metadata từ store.
    
    Args:
        store_path: Đường dẫn đến backup store
        snapshot_id: Snapshot ID
        skip_rollback_check: If True, skip rollback check (used internally by list_snapshots)
    
    Returns:
        SnapshotMetadata object
    
    Raises:
        FileNotFoundError: Nếu snapshot không tồn tại
    """
    snapshot_path = os.path.join(store_path, "snapshots", f"{snapshot_id}.json")
    with open(snapshot_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    current = SnapshotMetadata(
        id=data["id"],
        label=data["label"],
        timestamp=data["timestamp"],
        merkle_root=data["merkle_root"],
        prev_root=data["prev_root"],
        manifest_hash=data["manifest_hash"]
    )

    # ===== CHỐNG ROLLBACK =====
    # Skip rollback check when called from list_snapshots to avoid infinite recursion
    if not skip_rollback_check and current.prev_root:
        snapshots = list_snapshots(store_path)
        previous = None
        for s in snapshots:
            if s.timestamp < current.timestamp:
                previous = s

        if previous and current.prev_root != previous.merkle_root:
            raise RollbackDetected(
                f"Rollback detected at snapshot {current.id}"
            )

    return current


def list_snapshots(store_path: str) -> List[SnapshotMetadata]:
    """
    Liệt kê tất cả snapshots, sắp xếp theo timestamp (cũ nhất trước).
    
    Args:
        store_path: Đường dẫn đến backup store
    
    Returns:
        Danh sách SnapshotMetadata objects
    """
    snapshots_dir = os.path.join(store_path, "snapshots")
    snapshots = []
    
    if not os.path.exists(snapshots_dir):
        return snapshots
    
    for filename in os.listdir(snapshots_dir):
        if filename.endswith(".json") and filename.startswith("snapshot_"):
            snapshot_id = filename[:-5]  # Remove .json
            # Skip rollback check to avoid infinite recursion
            snapshot = load_snapshot(store_path, snapshot_id, skip_rollback_check=True)
            snapshots.append(snapshot)
    
    snapshots.sort(key=lambda s: s.timestamp)
    return snapshots


def get_latest_snapshot(store_path: str) -> Optional[SnapshotMetadata]:
    """
    Lấy snapshot mới nhất (để lấy prev_root).
    
    Args:
        store_path: Đường dẫn đến backup store
    
    Returns:
        SnapshotMetadata mới nhất hoặc None nếu không có snapshot nào
    """
    snapshots = list_snapshots(store_path)
    if not snapshots:
        return None
    return snapshots[-1]


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
    manifests_dir = os.path.join(store_path, "manifests")
    manifest_path = os.path.join(manifests_dir, f"{manifest_hash}.json")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    return manifest
