import hashlib
from typing import Optional


def sha256_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def has_changed(old_hash: Optional[str], new_hash: Optional[str]) -> bool:
    if old_hash is None and new_hash is None:
        return False
    return old_hash != new_hash