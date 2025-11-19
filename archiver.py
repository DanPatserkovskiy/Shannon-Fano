import os
import json
from typing import Optional, List, Dict
from compressor import ShannonFanoCompressor
from decompressor import ShannonFanoDecompressor
from access_control import AccessControl


class FileEntry:
    def __init__(self, filename: str, size: int, compressed_size: int,
                 metadata: Dict, codes: Dict[int, str], padding: int):
        self.filename = filename
        self.size = size
        self.compressed_size = compressed_size
        self.metadata = metadata
        self.codes = codes
        self.padding = padding


class FileArchiver:
    SIGNATURE = b'SFv3'
    def __init__(self):
        self.compressor = ShannonFanoCompressor()
        self.decompressor = ShannonFanoDecompressor()
        self.access_control = AccessControl()

    def _get_file_metadata(self, filepath: str) -> Dict:
        stat = os.stat(filepath)
        return {
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'atime': stat.st_atime,
            'mode': stat.st_mode
        }

    def compress_files(self, paths: List[str], password: Optional[str] = None) -> bool:
        try:
            file_entries = []
            all_compressed_data = bytearray()
            password_hash = None
            if password:
                password_hash = self.access_control.set_password(password)
                print(f"Архив защищен паролем")
            for path in paths:
                if os.path.isfile(path):
                    self._process_file(path, file_entries, all_compressed_data)
                elif os.path.isdir(path):
                    self._process_directory(path, file_entries, all_compressed_data)
            output_name = "archive.sf"
            if len(paths) == 1 and os.path.isfile(paths[0]):
                output_name = paths[0] + '.sf'
            with open(output_name, 'wb') as f:
                f.write(self.SIGNATURE)
                access_header = {
                    'password_protected': password is not None,
                    'password_hash': password_hash.hex() if password_hash else None,
                    'file_count': len(file_entries)
                }
                access_data = json.dumps(access_header).encode('utf-8')
                f.write(len(access_data).to_bytes(4, 'big'))
                f.write(access_data)
                for entry in file_entries:
                    file_header = {
                        'filename': entry.filename,
                        'size': entry.size,
                        'compressed_size': entry.compressed_size,
                        'metadata': entry.metadata,
                        'padding': entry.padding
                    }
                    header_data = json.dumps(file_header).encode('utf-8')
                    f.write(len(header_data).to_bytes(4, 'big'))
                    f.write(header_data)
                    codes_data = self.compressor._serialize_codes(entry.codes)
                    f.write(len(codes_data).to_bytes(4, 'big'))
                    f.write(codes_data)
                f.write(all_compressed_data)
            self._print_statistics(file_entries)
            print(f"Создан архив: {output_name}")
            return True
        except Exception as e:
            print(f"Ошибка при сжатии: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _process_file(self, filepath: str, file_entries: List, all_compressed_data: bytearray):
        with open(filepath, 'rb') as f:
            data = f.read()
        metadata = self._get_file_metadata(filepath)
        compressed_data, codes, padding = self.compressor.compress_data(data)
        file_entries.append(FileEntry(
            filename=os.path.basename(filepath),
            size=len(data),
            compressed_size=len(compressed_data),
            metadata=metadata,
            codes=codes,
            padding=padding
        ))
        all_compressed_data.extend(compressed_data)

    def _process_directory(self, directory: str, file_entries: List, all_compressed_data: bytearray):
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                self._process_file(filepath, file_entries, all_compressed_data)

    def _print_statistics(self, file_entries: List[FileEntry]):
        print("\nСтатистика сжатия:")
        total_original = 0
        total_compressed = 0
        for entry in file_entries:
            if entry.size == 0:
                ratio = 0.0
            else:
                ratio = (1 - entry.compressed_size / entry.size) * 100
            total_original += entry.size
            total_compressed += entry.compressed_size
            print(f"{entry.filename}:")
            print(f"Исходный: {entry.size} байт")
            print(f"Сжатый: {entry.compressed_size} байт")
            print(f"Сжатие: {ratio:.1f}%")
            print()
        if total_original == 0:
            total_ratio = 0.0
        else:
            total_ratio = (1 - total_compressed / total_original) * 100

        print(f"В итоге: {total_original} => {total_compressed} байт ({total_ratio:.1f}%)")

    def decompress_file(self, input_path: str, password: Optional[str] = None) -> bool:
        try:
            with open(input_path, 'rb') as f:
                signature = f.read(4)
                if signature != self.SIGNATURE:
                    print("Ошибка: неверный формат файла")
                    return False
                access_size = int.from_bytes(f.read(4), 'big')
                access_data = f.read(access_size)
                access_header = json.loads(access_data.decode('utf-8'))
                if access_header['password_protected']:
                    if not password:
                        password = input("Введите пароль для распаковки: ")
                    password_hash = bytes.fromhex(access_header['password_hash'])
                    if not self.access_control.verify_password(password, password_hash):
                        print("Ошибка: неверный пароль")
                        return False
                    print("Пароль верный, распаковываю...")
                file_entries = []
                total_compressed_size = 0
                for i in range(access_header['file_count']):
                    header_size_bytes = f.read(4)
                    if len(header_size_bytes) < 4:
                        break
                    header_size = int.from_bytes(header_size_bytes, 'big')
                    header_data = f.read(header_size)
                    if len(header_data) < header_size:
                        break
                    file_info = json.loads(header_data.decode('utf-8'))
                    codes_size_bytes = f.read(4)
                    if len(codes_size_bytes) < 4:
                        break
                    codes_size = int.from_bytes(codes_size_bytes, 'big')
                    codes_data = f.read(codes_size)
                    if len(codes_data) < codes_size:
                        break
                    codes, _ = self.decompressor._deserialize_codes(codes_data)
                    file_info['codes'] = codes
                    file_entries.append(file_info)
                    total_compressed_size += file_info['compressed_size']
                current_pos = f.tell()
                compressed_data = f.read()
                self._extract_files(file_entries, compressed_data)
                return True
        except Exception as e:
            print(f"Ошибка при распаковке: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _extract_files(self, file_entries: List[Dict], compressed_data: bytes):
        data_offset = 0
        for file_info in file_entries:
            try:
                file_compressed_data = compressed_data[data_offset:data_offset + file_info['compressed_size']]
                decompressed = self.decompressor.decompress_data(
                    file_compressed_data,
                    file_info['codes'],
                    file_info['padding'],
                    file_info['size']
                )
                filename = file_info['filename']
                os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
                with open(filename, 'wb') as out_file:
                    out_file.write(decompressed)
                print(f"Распакован: {filename} ({len(decompressed)}/{file_info['size']} байт)")
                data_offset += file_info['compressed_size']
            except Exception as e:
                print(f"Ошибка при обработке файла {file_info['filename']}: {e}")
                import traceback
                traceback.print_exc()
                continue