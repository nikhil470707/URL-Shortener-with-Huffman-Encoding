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
    self.max_collision_attempts = 10  # Limit attempts to find unique short code

  def _generate_short_code(self, url: str) -> str:
    hash_object = hashlib.sha256(url.encode())
    hash_hex = hash_object.hexdigest()

    for _ in range(self.max_collision_attempts):
      short_code = base64.urlsafe_b64encode(bytes.fromhex(hash_hex[:16])).decode('utf-8').rstrip('=')[:8]
      short_code += ''.join(random.choices(string.ascii_lowercase, k=4))  # Append random string
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

    # Pad binary string to multiple of 8
    padding_length = (8 - len(compressed) % 8) % 8
    padded_binary = compressed + '0' * padding_length

    # Convert to bytes and then to base64
    bytes_data = int(padded_binary, 2).to_bytes((len(padded_binary) + 7) // 8, byteorder='big')
    compressed_str = base64.urlsafe_b64encode(bytes_data).decode()

    return compressed_str, huffman_codes

  def _decompress(self, compressed_str: str, huffman_codes: Dict[str, str]) -> str:
    # Create reverse mapping
    reverse_codes = {code: char for char, code in huffman_codes.items()}

    # Convert from base64 to binary
    bytes_data = base64.urlsafe_b64decode(compressed_str.encode())
    binary = bin(int.from_bytes(bytes_data, byteorder='big'))[2:].zfill(len(bytes_data) * 8)

    # Decode
    result = []
    current_code = ''
    for bit in binary:
      current_code += bit
      if current_code in reverse_codes:
        result.append(reverse_codes[current_code])
        current_code = ''

    return ''.join(result)

  def shorten_url(self, long_url: str) -> Tuple[str, str]:
    # Check if URL already exists
    if long_url in self.url_to_code:
      short_code = self.url_to_code[long_url]
      compressed_info = self.compressed_data[short_code]
      return short_code, compressed_info['compressed']

    # Generate new short code
    short_code = self._generate_short_code(long_url)

    # Store mappings
    self.url_to_code[long_url] = short_code
    self.code_to_url[short_code] = long_url

    # Compress and store compression info with unique identifier
    compressed_str, huffman_codes = self._compress(short_code)
    self.compressed_data[short_code] = {
      'compressed': compressed_str,
      'huffman_codes': huffman_codes,
      'original_url': long_url
    }

    return short_code, compressed_str

  def expand_url(self, compressed_code: str) -> Optional[str]:
    for short_code, data in self.compressed_data.items():
      try:
        decompressed = self._decompress(compressed_code, data['huffman_codes'])
        if decompressed in self.code_to_url and self.code_to_url[decompressed] == data['original_url']:
          return self.code_to_url[decompressed]
      except Exception:
        pass
    return None

class HuffmanNode:
  def __init__(self, char: str = '', freq: int = 0):
    self.char = char
    self.freq = freq
    self.left = None
    self.right = None

  def __lt__(self, other):
    return self.freq < other.freq

# Example usage
if __name__ == "__main__":
  shortener = URLShortener()

  test_urls = [
    "https://www.example.com/very/long/path/to/resource?param1=value1&param2=value2",
    "https://another-example.com/blog/post/2024/01/15/how-to-implement-url-shortener",
    "https://third-example.net/products/category/subcategory/item?id=12345&sort=price"
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