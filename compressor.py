from collections import Counter
from typing import Dict, List, Tuple
from nodes import ShannonFanoNode

class ShannonFanoCompressor:
    def __init__(self):
        self.codes = {}

    def calculate_frequencies(self, data: bytes) -> Dict[int, int]:
        return Counter(data)

    def build_shannon_fano_tree(self, frequencies: Dict[int, int]) -> ShannonFanoNode:
        nodes = [ShannonFanoNode(symbol, freq) for symbol, freq in frequencies.items()]
        nodes.sort(key=lambda x: x.frequency, reverse=True)
        def build_subtree(nodes_list: List[ShannonFanoNode]) -> ShannonFanoNode:
            if len(nodes_list) == 1:
                return nodes_list[0]
            total_freq = sum(node.frequency for node in nodes_list)
            current_freq = 0
            split_index = 0
            min_diff = float('inf')
            for i in range(1, len(nodes_list)):
                current_freq += nodes_list[i - 1].frequency
                diff = abs(2 * current_freq - total_freq)
                if diff < min_diff:
                    min_diff = diff
                    split_index = i
            left_nodes = nodes_list[:split_index]
            right_nodes = nodes_list[split_index:]
            parent = ShannonFanoNode(frequency=total_freq)
            parent.left = build_subtree(left_nodes)
            parent.right = build_subtree(right_nodes)
            return parent
        return build_subtree(nodes)

    def generate_codes(self, node: ShannonFanoNode, current_code: str = ""):
        if node is None:
            return
        if node.symbol is not None:
            self.codes[node.symbol] = current_code
            return
        self.generate_codes(node.left, current_code + "0")
        self.generate_codes(node.right, current_code + "1")

    def compress_data(self, data: bytes) -> Tuple[bytes, Dict[int, str], int]:
        if not data:
            print("Пустые входные данные")
            return b'', {}, 0
        frequencies = self.calculate_frequencies(data)
        if len(frequencies) == 0:
            print("Нет частот")
            return b'', {}, 0
        root = self.build_shannon_fano_tree(frequencies)
        self.codes = {}
        self.generate_codes(root)
        encoded_bits = ''.join(self.codes[byte] for byte in data)
        padding_bits = (8 - len(encoded_bits) % 8) % 8
        encoded_bits += '0' * padding_bits
        compressed_bytes = bytearray()
        for i in range(0, len(encoded_bits), 8):
            byte_str = encoded_bits[i:i + 8]
            compressed_bytes.append(int(byte_str, 2))
        return bytes(compressed_bytes), self.codes, padding_bits

    def _serialize_codes(self, codes: Dict[int, str]) -> bytes:
        result = bytearray()
        result.extend(len(codes).to_bytes(2, 'big'))
        for symbol, code in codes.items():
            result.append(symbol)
            code_length = len(code)
            result.append(code_length)
            code_bytes = self._bits_to_bytes(code)
            result.extend(code_bytes)
        return bytes(result)

    def _bits_to_bytes(self, bits: str) -> bytes:
        result = bytearray()
        padded_length = (len(bits) + 7) // 8 * 8
        padded_bits = bits.ljust(padded_length, '0')
        for i in range(0, len(padded_bits), 8):
            byte_str = padded_bits[i:i + 8]
            result.append(int(byte_str, 2))
        return bytes(result)