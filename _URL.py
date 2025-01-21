import collections
import heapq
import hashlib
import base64
import json
from typing import Dict, Optional, Tuple
import random
import string
from collections import Counter


class URLShortener:
    def __init__(self):
        self.url_to_code: Dict[str, str] = {}
        self.code_to_url: Dict[str, str] = {}
        self.compressed_data: Dict[str, Dict] = {}
        self.max_collision_attempts = 10

    def _generate_short_code(self, url: str) -> str:
        hash_object = hashlib.sha256(url.encode())
        hash_hex = hash_object.hexdigest()

        for _ in range(self.max_collision_attempts):
            short_code = base64.urlsafe_b64encode(bytes.fromhex(hash_hex[:16])).decode('utf-8').rstrip('=')[:8]
            short_code += ''.join(random.choices(string.ascii_lowercase, k=4)) 
            if short_code not in self.code_to_url:
                return short_code

        raise ValueError("Failed to generate unique short code after multiple attempts")

    def _build_huffman_tree(self, data: str) -> Dict[str, str]:
        freq = Counter(data)

        if len(freq) == 1:
            return {data[0]: '0'}

        heap = []
        for char, count in freq.items():
            heapq.heappush(heap, HuffmanNode(char, count))

        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            internal = HuffmanNode(freq=left.freq + right.freq)
            internal.left = left
            internal.right = right
            heapq.heappush(heap, internal)

        codes = {}

        def generate_codes(node, code=''):
            if node.char:
                codes[node.char] = code
                return
            if node.left:
                generate_codes(node.left, code + '0')
            if node.right:
                generate_codes(node.right, code + '1')

        if heap:
            generate_codes(heap[0])
        return codes

    def _compress(self, data: str) -> Tuple[str, Dict[str, str]]:
        huffman_codes = self._build_huffman_tree(data)

        compressed = ''.join(huffman_codes[char] for char in data)

        padding_length = (8 - len(compressed) % 8) % 8
        padded_binary = compressed + '0' * padding_length

        bytes_data = int(padded_binary, 2).to_bytes((len(padded_binary) + 7) // 8, byteorder='big')
        compressed_str = base64.urlsafe_b64encode(bytes_data).decode()

        return compressed_str, huffman_codes

    def _decompress(self, compressed_str: str, huffman_codes: Dict[str, str]) -> str:
        reverse_codes = {code: char for char, code in huffman_codes.items()}

        bytes_data = base64.urlsafe_b64decode(compressed_str.encode())
        binary = bin(int.from_bytes(bytes_data, byteorder='big'))[2:].zfill(len(bytes_data) * 8)

        result = []
        current_code = ''
        for bit in binary:
            current_code += bit
            if current_code in reverse_codes:
                result.append(reverse_codes[current_code])
                current_code = ''

        return ''.join(result)

    def shorten_url(self, long_url: str) -> Tuple[str, str]:
        if long_url in self.url_to_code:
            short_code = self.url_to_code[long_url]
            compressed_info = self.compressed_data[short_code]
            return short_code, compressed_info['compressed']

        short_code = self._generate_short_code(long_url)

        while short_code in self.code_to_url:
            short_code = self._generate_short_code(long_url + random.choice(string.ascii_letters))

        self.url_to_code[long_url] = short_code
        self.code_to_url[short_code] = long_url

        compressed_str, huffman_codes = self._compress(short_code)
        self.compressed_data[compressed_str] = {
            'huffman_codes': huffman_codes,
            'original_url': long_url
        }

        return short_code, compressed_str

    def expand_url(self, compressed_code: str) -> Optional[str]:
        if compressed_code not in self.compressed_data:
            return None

        data = self.compressed_data[compressed_code]
        huffman_codes = data['huffman_codes']
        try:
            short_code = self._decompress(compressed_code, huffman_codes)
        except Exception:
            return None

        return self.code_to_url.get(short_code)

class HuffmanNode:
    def __init__(self, char: str = '', freq: int = 0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


if __name__ == "__main__":
    shortener = URLShortener()

    test_urls = [
        
    ]

    print("Testing URL Shortener with Huffman Encoding:\n")

    for url in test_urls:
        print(f"Original URL: {url}")
        short_code, compressed = shortener.shorten_url(url)
        print(f"Short Code: {short_code}")
        print(f"Compressed Code: {compressed}")

        expanded = shortener.expand_url(compressed)
        print(f"Expanded URL: {expanded}")
        print(f"Matches original: {expanded == url}\n")
