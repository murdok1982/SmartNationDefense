import secrets
import os

def generate_fernet_key() -> bytes:
    from cryptography.fernet import Fernet
    return Fernet.generate_key()

def generate_secret_key(length: int = 64) -> str:
    return secrets.token_hex(length // 2)

def main():
    fernet_key = generate_fernet_key()
    secret_key = generate_secret_key()

    with open("fernet.key", "wb") as f:
        f.write(fernet_key)

    env_lines = [
        f"SECRET_KEY={secret_key}",
        f"FERNET_KEY_PATH=./fernet.key",
    ]

    print("=" * 60)
    print("  SESIS-FEDERATION — Claves generadas")
    print("=" * 60)
    print(f"\n  FERNET_KEY  -> fernet.key ({len(fernet_key)} bytes)")
    print(f"  SECRET_KEY  -> {secret_key[:16]}...{secret_key[-16:]}")
    print(f"\n  Añade al archivo .env:")
    for line in env_lines:
        print(f"    {line}")
    print("=" * 60)

if __name__ == "__main__":
    main()
