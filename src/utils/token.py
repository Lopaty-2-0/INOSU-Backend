import os
import time
import hmac
import base64
import hashlib

ip = os.getenv("HMAC_IP")
hmac_secret = os.getenv("HMAC_SECRET")
expiresIn = 600

def generate_hmac_token(file_path: str, expires_in: int = expiresIn) -> str:
    expiry_timestamp = int(time.time()) + expires_in
    payload = f"{file_path}:{expiry_timestamp}"

    sig = hmac.new(
        hmac_secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).digest()

    sig_hex = sig.hex()
    token_str = f"{payload}:{sig_hex}"
    token = base64.urlsafe_b64encode(token_str.encode()).decode().rstrip("=")
    return token