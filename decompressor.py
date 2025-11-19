from typing import Dict, Tuple


class ShannonFanoDecompressor:
    def __init__(self):
        self.reverse_codes = {}

    def _deserialize_codes(self, data: bytes) -> Tuple[Dict[int, str], int]:
        codes = {}
        offset = 0
        if len(data) < 2:
            return codes, offset
        codes_count = int.from_bytes(data[offset:offset + 2], 'big')
        offset += 2
        for _ in range(codes_count):
            if offset >= len(data):
                break
            symbol = data[offset]
            offset += 1
            if offset >= len(data):
                break
            code_length = data[offset]
            offset += 1
            bytes_needed = (code_length + 7) // 8
            if offset + bytes_needed > len(data):
                break
            code_bytes = data[offset:offset + bytes_needed]
            offset += bytes_needed
            code = self._bytes_to_bits(code_bytes, code_length)
            codes[symbol] = code
        return codes, offset

    def _bytes_to_bits(self, data: bytes, bit_length: int) -> str:
        bits = ''.join(f'{byte:08b}' for byte in data)
        return bits[:bit_length]

    def decompress_data(self, compressed_data: bytes, codes: Dict[int, str],
                        padding_bits: int, original_size: int) -> bytes:
        if not compressed_data or not codes:
            print("Нет данных или кодов для распаковки")
            return b''
        print(f"Было: {len(compressed_data)} байт")
        print(f"Итоговый размер: {original_size} байт")
        reverse_codes = {v: k for k, v in codes.items()}
        bit_string = ''.join(f'{byte:08b}' for byte in compressed_data)
        if padding_bits > 0:
            bit_string = bit_string[:-padding_bits]
        result = bytearray()
        current_bits = ''
        for bit in bit_string:
            current_bits += bit
            if current_bits in reverse_codes:
                result.append(reverse_codes[current_bits])
                current_bits = ''
                if len(result) == original_size:
                    break
        return bytes(result)