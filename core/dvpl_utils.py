"""DVPL codec (World of Tanks Blitz container).

Footer (20 bytes, little-endian):
  [0:4]   original_size
  [4:8]   compressed_size
  [8:12]  crc32(compressed)
  [12:16] compression_type (0=NONE, 1=LZ4, 2=LZ4_HC)
  [16:20] b'DVPL'
"""
import os
import zlib

import lz4.block

MAGIC_DVPL = b'DVPL'
FOOTER_SIZE = 20

DVPL_TYPE_NONE = 0
DVPL_TYPE_LZ4 = 1
DVPL_TYPE_LZ4_HC = 2


def write_dvpl(filepath, data, compression_type=None):
    """Compress bytes and write a DVPL file."""
    input_data = data
    if compression_type is None:
        compression_type = DVPL_TYPE_LZ4_HC

    if compression_type == DVPL_TYPE_LZ4_HC:
        try:
            compressed = lz4.block.compress(input_data, store_size=False, mode='high_compression')
            comp_type = DVPL_TYPE_LZ4_HC if len(compressed) < len(input_data) else DVPL_TYPE_NONE
            if comp_type == DVPL_TYPE_NONE:
                compressed = input_data
        except Exception:
            compressed = input_data
            comp_type = DVPL_TYPE_NONE
    elif compression_type == DVPL_TYPE_LZ4:
        try:
            compressed = lz4.block.compress(input_data, store_size=False, mode='fast')
            comp_type = DVPL_TYPE_LZ4 if len(compressed) < len(input_data) else DVPL_TYPE_NONE
            if comp_type == DVPL_TYPE_NONE:
                compressed = input_data
        except Exception:
            compressed = input_data
            comp_type = DVPL_TYPE_NONE
    else:
        compressed = input_data
        comp_type = DVPL_TYPE_NONE

    original_size = len(input_data)
    compressed_size = len(compressed)
    crc32_val = zlib.crc32(compressed) & 0xFFFFFFFF

    footer = bytearray(FOOTER_SIZE)
    footer[:4] = original_size.to_bytes(4, 'little')
    footer[4:8] = compressed_size.to_bytes(4, 'little')
    footer[8:12] = crc32_val.to_bytes(4, 'little')
    footer[12:16] = comp_type.to_bytes(4, 'little')
    footer[16:] = MAGIC_DVPL

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    if os.path.exists(filepath):
        try:
            import stat as _stat
            os.chmod(filepath, _stat.S_IWRITE | _stat.S_IREAD)
        except Exception:
            pass
    with open(filepath, 'wb') as f:
        f.write(compressed + footer)


def read_dvpl(filepath):
    """Read a file. Returns (payload_bytes, compression_type or None if not DVPL)."""
    with open(filepath, 'rb') as f:
        buffer = f.read()

    if len(buffer) < FOOTER_SIZE or buffer[-4:] != MAGIC_DVPL:
        return buffer, None

    footer = buffer[-FOOTER_SIZE:]
    original_size = int.from_bytes(footer[:4], 'little')
    compressed_size = int.from_bytes(footer[4:8], 'little')
    crc32_val = int.from_bytes(footer[8:12], 'little')
    comp_type = int.from_bytes(footer[12:16], 'little')

    compressed_block = buffer[:-FOOTER_SIZE]
    if len(compressed_block) != compressed_size:
        return buffer, None
    if crc32_val != (zlib.crc32(compressed_block) & 0xFFFFFFFF):
        return buffer, None

    if comp_type == DVPL_TYPE_NONE:
        if original_size != compressed_size:
            return buffer, None
        return compressed_block, comp_type
    if comp_type in (DVPL_TYPE_LZ4, DVPL_TYPE_LZ4_HC):
        try:
            decompressed = lz4.block.decompress(compressed_block, uncompressed_size=original_size)
            if len(decompressed) != original_size:
                return buffer, None
            return decompressed, comp_type
        except Exception:
            return buffer, None
    return buffer, None


def is_dvpl_file(filepath):
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, 'rb') as f:
            f.seek(-4, os.SEEK_END)
            return f.read(4) == MAGIC_DVPL
    except Exception:
        return False


def decompress_dvpl_to_text(filepath, encoding='utf-8'):
    data, _ = read_dvpl(filepath)
    for enc in ('utf-8-sig', 'utf-8', 'cp1251', 'latin-1', 'cp866'):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='replace'), 'utf-8'


def compress_text_to_dvpl(filepath, text, encoding='utf-8', compression_type=None):
    data = text.encode(encoding)
    write_dvpl(filepath, data, compression_type)
