import argon2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

# Configure Argon2id password hasher with recommended parameters
_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    type=argon2.Type.ID
)


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password using Argon2id.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.
    Returns True if valid, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


hash_password = get_password_hash

