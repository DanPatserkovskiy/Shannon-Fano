from typing import Optional

class ShannonFanoNode:
    def __init__(self, symbol: Optional[int] = None, frequency: int = 0):
        self.symbol = symbol
        self.frequency = frequency
        self.left = None
        self.right = None

    def __repr__(self):
        if self.symbol is not None:
            return f"Node(symbol={chr(self.symbol) if 32 <= self.symbol <= 126 else self.symbol}, freq={self.frequency})"
        return f"Node(internal, freq={self.frequency})"