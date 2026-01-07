"""
Merkle tree module - MEMBER 2

Nhiệm vụ:
- Tính Merkle root từ manifest (binary tree)
- Verify Merkle root
- PHẢI document thuật toán trong README.md

Tham khảo: src/interfaces.py
"""

# TODO: Implement compute_merkle_root(), verify_merkle_root()
# TODO: Document thuật toán Merkle trong README.md

from typing import List, Dict, Tuple, Optional
import hashlib
def _hash_file_entry(file_entry: dict) -> str:
    data = file_entry["path"] + ":" + "".join(file_entry["chunks"])
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
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
    file_hashes = [_hash_file_entry(file) for file in manifest["files"]]
    
    if not file_hashes:
        return ""
    
    while len(file_hashes) > 1:
        if len(file_hashes) % 2 != 0:
            file_hashes.append(file_hashes[-1])
        
        new_level = []
        for i in range(0, len(file_hashes), 2):
            combined = file_hashes[i] + file_hashes[i + 1]
            new_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
            new_level.append(new_hash)
        
        file_hashes = new_level
    
    return file_hashes[0]



def verify_merkle_root(manifest: dict, expected_root: str) -> bool:
    """
    Xác minh Merkle root của manifest.
    
    Args:
        manifest: Manifest cần xác minh
        expected_root: Merkle root mong đợi
    
    Returns:
        True nếu khớp, False nếu không
    """
    computed_root = compute_merkle_root(manifest)
    return computed_root == expected_root
