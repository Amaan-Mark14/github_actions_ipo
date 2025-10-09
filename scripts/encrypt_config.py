# scripts/encrypt_config.py
from cryptography.fernet import Fernet
import json
import os

def generate_key():
    """Generate a new encryption key"""
    return Fernet.generate_key()

def encrypt_config():
    # Read the encryption key (create if doesn't exist)
    key_file = '.config.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            encryption_key = f.read()
    else:
        encryption_key = generate_key()
        with open(key_file, 'wb') as f:
            f.write(encryption_key)
        print(f"Generated new encryption key: {encryption_key.decode()}")
        print("Store this key in GitHub Secrets as CONFIG_ENCRYPTION_KEY")

    # Read the unencrypted config
    with open('config/recipients.json', 'r') as f:
        config = json.load(f)

    # Encrypt the config
    fernet = Fernet(encryption_key)
    encrypted_data = fernet.encrypt(json.dumps(config).encode())

    # Save the encrypted config
    with open('config/recipients.enc.json', 'wb') as f:
        f.write(encrypted_data)
    
    print("Config encrypted successfully!")

if __name__ == "__main__":
    encrypt_config()

# scripts/decrypt_config.py
from cryptography.fernet import Fernet
import json

def decrypt_config(encryption_key):
    # Read the encrypted config
    with open('config/recipients.enc.json', 'rb') as f:
        encrypted_data = f.read()

    # Decrypt the config
    fernet = Fernet(encryption_key)
    decrypted_data = fernet.decrypt(encrypted_data)
    config = json.loads(decrypted_data)

    print("Decrypted config:")
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    # For testing, read key from local file
    with open('.config.key', 'rb') as f:
        key = f.read()
    decrypt_config(key)