import os
import struct

MAGIC_NUMBER = b"4337PRJ3"
BLOCK_SIZE = 512

class IndexFile:
    def __init__(self):
        self.file = None

    def create_index_file(self, file_path):
        if os.path.exists(file_path):
            overwrite = input(f"File {file_path} already exists. Overwrite? (y/n): ").strip().lower()
            if overwrite != "y":
                print("File creation aborted.")
                return
        self.file = open(file_path, "wb+")
        self._write_header()

    def open_index_file(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist.")
        self.file = open(file_path, "rb+")
        self._validate_header()

    def _write_header(self):
        header = struct.pack(
            f">{len(MAGIC_NUMBER)}sQQ",
            MAGIC_NUMBER,
            0,  # root_block_id
            1   # next_block_id
        )
        self.file.write(header + b"\x00" * (BLOCK_SIZE - len(header)))
        self.file.flush()

    def _validate_header(self):
        self.file.seek(0)
        header = self.file.read(BLOCK_SIZE)
        magic, root_block_id, next_block_id = struct.unpack(f">{len(MAGIC_NUMBER)}sQQ", header[:24])
        if magic != MAGIC_NUMBER:
            raise ValueError("Invalid file format.")

    def close(self):
        if self.file:
            self.file.close()
            self.file = None
