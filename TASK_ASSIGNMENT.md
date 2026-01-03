# PHÂN CÔNG CÔNG VIỆC cụ thể

- **`src/interfaces.py`** - ĐỌC ĐẦU TIÊN! (function signatures)
- **`README.md`** - Thuật toán, quy ước

## MEMBER 1: STORAGE & CHUNKING

**Files:**
- `src/core/chunker.py` - Chia file thành chunks 1 MiB
- `src/core/storage.py` - Content-addressable storage + deduplication
- `src/utils/hash.py` - SHA-256 hashing
- `tests/test_core/test_storage.py` - Unit tests

**Deliverables:**
- Chunking hoạt động
- Storage lưu/đọc chunks theo hash
- Deduplication tự động

---

## MEMBER 2: MANIFEST & MERKLE TREE

**Files:**
- `src/core/manifest.py` - Canonical manifest (JSON deterministic)
- `src/core/merkle.py` - Merkle tree (binary tree)
- `src/core/snapshot.py` - Snapshot metadata management
- `tests/test_core/test_manifest.py` - Unit tests

**Deliverables:**
- Canonical manifest (deterministic)
- Merkle tree implementation
- Snapshot management + anti-rollback (prev_root)
- Document thuật toán Merkle trong README.md

---

## MEMBER 3: CLI & INTEGRATION

**Files:**
- `src/core/journal.py` - Journal/WAL (crash consistency)
- `src/cli/main.py` - CLI entry point (argparse)
- `src/cli/commands.py` - 6 commands implementation
- `tests/test_integration/test_required_scenarios.py` - 7 required tests

**Deliverables:**
- Journal/WAL hoạt động (với fsync)
- CLI đầy đủ 6 commands (init, backup, list-snapshots, verify, restore, audit-verify)
- Integration tất cả modules (Member 1, 2, 4)
- 7 test scenarios bắt buộc pass

**7 Test Scenarios Bắt Buộc:**
1. Restore integrity (xóa files, restore, so sánh)
2. Chunk corruption (sửa 1 byte → verify FAIL)
3. Manifest corruption (sửa manifest → verify FAIL)
4. Rollback detection (thay snapshot mới bằng cũ → phát hiện)
5. Crash consistency (kill backup → store OK)
6. Policy enforcement (lệnh không được phép → DENY)
7. Audit tampering (sửa audit.log → CORRUPTED)

---

## MEMBER 4: SECURITY

**Files:**
- `src/security/user.py` - OS user identification
- `src/security/policy.py` - Policy enforcement (YAML)
- `src/security/audit.py` - Audit log + hash chain
- `tests/test_security/test_all.py` - Unit tests
- `policy.yaml` - Update với team usernames

**Deliverables:**
- User identification (OS-based)
- Policy enforcement (3 roles: admin, operator, auditor)
- Audit log với hash chain (tamper-evident)
