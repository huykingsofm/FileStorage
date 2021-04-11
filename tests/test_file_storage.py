import os
import shutil
from file_storage.util import Util
from file_storage import FileStorage
from bytes_encryptor import BytesEncryptor
from bytes_encryptor.generator import BytesGenerator

from hks_pylib.cryptography.symmetrics import AES_CBC


def test_file_storage():
    key = b"0123456789abcdef"
    iv = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
    cipher = AES_CBC(key)
    cipher.set_param(0, iv)
    encryptor = BytesEncryptor(cipher)
    
    storage = FileStorage(
        "Storage",
        n_splits=100,
        identifier_size=100,
        force_reinitialize=True
    )
    for file in os.listdir("tests/imgs"):
        path = os.path.join("tests/imgs", file)
        if os.path.isfile(path):
            bytes_generator = BytesGenerator(path)
            encryptor.encrypt_to(bytes_generator, ".tmp")
            last_bytes = Util.get_identifier(".tmp", 100)
            new_path = storage.create_new_path(last_bytes)
            shutil.move(".tmp", new_path)
            storage.save_info(new_path)
    
    storage = FileStorage("Storage")
    for file in storage.iter(b"\x01\x02\x03"):
        print(file)


if __name__ == "__main__":
    test_file_storage()