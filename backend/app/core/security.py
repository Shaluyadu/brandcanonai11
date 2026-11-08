import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional
from app.core.config import settings

# Initialize Argon2id Hasher
try:
    from argon2 import PasswordHasher
    from argon2.low_level import Type
    from argon2.exceptions import VerifyMismatchError, VerificationError

    _argon2_hasher = PasswordHasher(
        time_cost=3,
        memory_cost=65536,  # 64 MiB
        parallelism=4,
        hash_len=32,
        type=Type.ID  # Explicit Argon2id
    )
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False
    _argon2_hasher = None


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2id.
    Fallbacks to PBKDF2-HMAC-SHA256 only if native Argon2id bindings are unavailable.
    """
    if not password:
        raise ValueError("Password cannot be empty")

    if HAS_ARGON2 and _argon2_hasher:
        return _argon2_hasher.hash(password)

    # Secure PBKDF2-HMAC-SHA256 fallback
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived).decode("ascii")
    return f"pbkdf2_sha256$100000${salt_b64}${hash_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plaintext password against an Argon2id or legacy PBKDF2 hash.
    """
    if not plain_password or not hashed_password:
        return False

    # Check Argon2id hash format
    if hashed_password.startswith("$argon2"):
        if not HAS_ARGON2 or not _argon2_hasher:
            return False
        try:
            return _argon2_hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError):
            return False
        except Exception:
            return False

    # Fallback PBKDF2 verification
    try:
        parts = hashed_password.split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            iterations = int(parts[1])
            salt = base64.b64decode(parts[2].encode("ascii"))
            expected_hash = base64.b64decode(parts[3].encode("ascii"))
            derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(derived, expected_hash)
    except Exception:
        pass

    return False


# --- Opaque Session Tokens & Hashing ---

def generate_session_token() -> str:
    """Generate cryptographically secure 256-bit URL-safe opaque session token."""
    return f"bcs_{secrets.token_urlsafe(32)}"


def hash_session_token(token: str) -> str:
    """
    SHA-256 hash of opaque session token before saving into user_sessions table.
    Database compromise will never reveal valid plaintext session tokens.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# --- RFC 7519 JWT Support ---

def _b64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_url_decode(data_str: str) -> bytes:
    padding = "=" * ((4 - len(data_str) % 4) % 4)
    return base64.urlsafe_b64decode((data_str + padding).encode("ascii"))


def create_access_token(data: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    to_encode = data.copy()
    now_epoch = int(time.time())
    exp = now_epoch + (expires_delta_seconds if expires_delta_seconds is not None else (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    to_encode["iat"] = now_epoch
    to_encode["exp"] = exp

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64_url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64_url_encode(json.dumps(to_encode, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64_url_encode(signature)}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64_url_decode(signature_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(_b64_url_decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp")
        if exp is not None and int(time.time()) > int(exp):
            return None

        return payload
    except Exception:
        return None
