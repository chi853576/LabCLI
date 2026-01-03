"""
Integration tests - ALL MEMBERS

7 TEST SCENARIOS BẮT BUỘC:
1. Restore integrity: xóa files, restore, so sánh
2. Chunk corruption: sửa 1 byte chunk → verify FAIL
3. Manifest corruption: sửa manifest → verify FAIL
4. Rollback detection: thay snapshot mới bằng cũ → phát hiện
5. Crash consistency: kill backup → store OK, no corrupted snapshot
6. Policy enforcement: chạy lệnh không được phép → DENY
7. Audit tampering: sửa audit.log → audit-verify FAIL

Tham khảo: Yêu cầu kiểm thử trong đề bài
"""

import pytest

# TODO: Implement 7 required test scenarios
