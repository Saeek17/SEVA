"""Print a fresh VAPID key pair for Web Push. Run: python -m scripts.generate_vapid"""
import base64

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid01


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


vapid = Vapid01()
vapid.generate_keys()
private_bytes = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
public_bytes = vapid.public_key.public_bytes(
    serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
)

print(f"VAPID_PUBLIC_KEY={_b64url(public_bytes)}")
print(f"VAPID_PRIVATE_KEY={_b64url(private_bytes)}")
