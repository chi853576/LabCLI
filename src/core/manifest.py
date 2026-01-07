"""
Manifest management module - MEMBER 2

Nhiệm vụ:
- Tạo canonical manifest (files sorted, JSON deterministic)
- Serialize manifest (sort_keys=True, separators=(',', ':'))
- Hash manifest

Tham khảo: src/interfaces.py, README.md (Canonical encoding)
"""

# TODO: Implement create_manifest(), serialize_manifest(), hash_manifest()
from typing import List, Dict, Tuple, Optional
import json
import hashlib
from src.interfaces import FileEntry
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
    sorted_entries = sorted(file_entries, key=lambda e: e.path)

    return {
        "files": [
            {
                "path": entry.path,
                "chunks": entry.chunks
            }
            for entry in sorted_entries
        ]
    }

def serialize_manifest(manifest: dict) -> str:
    """
    Serialize manifest thành chuỗi JSON canonical.
    Phải deterministic (cùng input → cùng output).
    
    Args:
        manifest: Manifest dict
    
    Returns:
        Chuỗi JSON (keys đã sắp xếp, không có khoảng trắng thừa)
    """
    return json.dumps(manifest, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def hash_manifest(manifest: dict) -> str:
    """
    Tính SHA-256 hash của canonical manifest.
    
    Args:
        manifest: Manifest dict
    
    Returns:
        SHA-256 hash của serialized manifest
    """
    serialized = serialize_manifest(manifest)
    sha256 = hashlib.sha256()
    sha256.update(serialized.encode('utf-8'))
    return sha256.hexdigest()
