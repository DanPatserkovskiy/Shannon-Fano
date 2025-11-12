import os
from typing import Optional
from compressor import ShannonFanoCompressor
from decompressor import ShannonFanoDecompressor

class FileArchiver:
    SIGNATURE = b'SFv1'
    def __init__(self):
        self.compressor = ShannonFanoCompressor()
        self.decompressor = ShannonFanoDecompressor()

    def compress_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        try:
            if not os.path.exists(input_path):
                print(f"Ошибка: файл '{input_path}' не существует")
                return False
            if output_path is None:
                output_path = input_path + '.sf'
            with open(input_path, 'rb') as f:
                original_data = f.read()
            original_filename = os.path.basename(input_path)
            original_size = len(original_data)
            compressed_data, codes, padding_bits = self.compressor.compress_data(original_data)
            if not compressed_data and original_data:
                print("Ошибка: не удалось сжать данные")
                return False
            with open(output_path, 'wb') as f:
                f.write(self.SIGNATURE)
                filename_bytes = original_filename.encode('utf-8')
                f.write(len(filename_bytes).to_bytes(2, 'big'))
                f.write(filename_bytes)
                f.write(original_size.to_bytes(8, 'big'))
                f.write(padding_bits.to_bytes(1, 'big'))
                codes_data = self.compressor._serialize_codes(codes)
                f.write(codes_data)
                f.write(compressed_data)
            compressed_size = os.path.getsize(output_path)
            print("Архивация прошла успешно")
            print(f"Размер исходного файла {original_size} байт")
            print(f"Размер сжатого файла: {compressed_size} байт")
            return True
        except Exception as e:
            print(f"Ошибка при сжатии: {e}")
            return False

    def decompress_file(self, input_path: str, output_path: Optional[str] = None) -> bool:
        try:
            with open(input_path, 'rb') as f:
                signature = f.read(4)
                if signature != self.SIGNATURE:
                    print("Ошибка: неверный формат файла")
                    return False
                filename_length = int.from_bytes(f.read(2), 'big')
                original_filename = f.read(filename_length).decode('utf-8')
                original_size = int.from_bytes(f.read(8), 'big')
                padding_bits = int.from_bytes(f.read(1), 'big')
                remaining_data = f.read()
            if output_path is None:
                output_path = original_filename
            print(f"Распаковка: {os.path.basename(input_path)} -> {output_path}")
            codes, codes_size = self.decompressor._deserialize_codes(remaining_data)
            compressed_data_start = codes_size
            compressed_data = remaining_data[compressed_data_start:]
            decompressed_data = self.decompressor.decompress_data(
                compressed_data, codes, padding_bits, original_size
            )
            with open(output_path, 'wb') as f:
                f.write(decompressed_data)
            print(f"Файл {output_path} распакован")
            return True
        except Exception as e:
            print(f"Ошибка при распаковке: {e}")
            return False