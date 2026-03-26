"""eit_scorer/utils/stable_hash.py"""
import hashlib


def stable_sha256(text: str) -> str:
    """
    SHA-256 hash of a string.
    Independent of Python's built-in hash() randomization (PYTHONHASHSEED).
    Used to fingerprint scoring traces for reproducibility proofs.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
