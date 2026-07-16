"""
Pure-Python Radiance HDR (.hdr) resize tool.
Reads RGBE format, resizes with numpy, writes back out.
Usage: python resize_hdr.py input.hdr output.hdr [width]
"""
import numpy as np
import struct
import sys
import os
from PIL import Image


def read_hdr(path):
    """Read a Radiance HDR file, return float32 RGB array (H, W, 3)."""
    with open(path, 'rb') as f:
        buf = f.read()

    # Parse header
    i = 0
    while i < len(buf):
        line_end = buf.index(b'\n', i)
        line = buf[i:line_end].decode('latin-1')
        i = line_end + 1
        if line == '':
            break

    # Read size line: -Y H +X W
    size_end = buf.index(b'\n', i)
    size_line = buf[i:size_end].decode('latin-1')
    i = size_end + 1
    parts = size_line.split()
    H = int(parts[1])
    W = int(parts[3])

    # Read scanlines (RLE encoded RGBE)
    rgbe = np.zeros((H, W, 4), dtype=np.uint8)

    for y in range(H):
        # Check for new RLE format
        r1, r2, g, b = buf[i], buf[i+1], buf[i+2], buf[i+3]
        i += 4
        if r1 == 2 and r2 == 2 and (g & 0x80) == 0:
            # New RLE scanline
            scanline_width = (g << 8) | b
            scanline = np.zeros((4, scanline_width), dtype=np.uint8)
            for ch in range(4):
                x = 0
                while x < scanline_width:
                    code = buf[i]; i += 1
                    if code > 128:
                        # Run
                        val = buf[i]; i += 1
                        count = code - 128
                        scanline[ch, x:x+count] = val
                        x += count
                    else:
                        # Non-run
                        scanline[ch, x:x+code] = list(buf[i:i+code])
                        i += code
                        x += code
            rgbe[y] = scanline.T
        else:
            # Old format (uncompressed)
            rgbe[y, 0] = [r1, r2, g, b]
            for x in range(1, W):
                rgbe[y, x] = [buf[i], buf[i+1], buf[i+2], buf[i+3]]
                i += 4

    # Convert RGBE to float32 RGB
    R = rgbe[:, :, 0].astype(np.float32)
    G = rgbe[:, :, 1].astype(np.float32)
    B = rgbe[:, :, 2].astype(np.float32)
    E = rgbe[:, :, 3].astype(np.float32)

    scale = 2.0 ** (E - 128.0 - 8.0)
    scale[rgbe[:, :, 3] == 0] = 0
    rgb = np.stack([R * scale, G * scale, B * scale], axis=2)
    return rgb


def write_hdr(path, rgb):
    """Write float32 RGB array to Radiance HDR file."""
    H, W = rgb.shape[:2]

    with open(path, 'wb') as f:
        # Header
        f.write(b'#?RADIANCE\n')
        f.write(b'FORMAT=32-bit_rle_rgbe\n')
        f.write(b'\n')
        f.write(f'-Y {H} +X {W}\n'.encode())

        # Convert to RGBE
        eps = 1e-9
        maxc = np.maximum(rgb[:, :, 0], np.maximum(rgb[:, :, 1], rgb[:, :, 2]))
        valid = maxc > eps

        exp = np.zeros((H, W), dtype=np.float32)
        exp[valid] = np.ceil(np.log2(maxc[valid] + eps))
        scale = np.zeros((H, W), dtype=np.float32)
        scale[valid] = 2.0 ** (exp[valid] - 8.0)
        scale[~valid] = 1.0

        R = np.clip(rgb[:, :, 0] / scale, 0, 255).astype(np.uint8)
        G = np.clip(rgb[:, :, 1] / scale, 0, 255).astype(np.uint8)
        B = np.clip(rgb[:, :, 2] / scale, 0, 255).astype(np.uint8)
        E = np.clip(exp + 128, 0, 255).astype(np.uint8)
        E[~valid] = 0

        rgbe = np.stack([R, G, B, E], axis=2)

        # Write scanlines (uncompressed for simplicity)
        for y in range(H):
            # New RLE header per scanline
            f.write(bytes([2, 2, (W >> 8) & 0xFF, W & 0xFF]))
            # Write each channel with simple run-length
            for ch in range(4):
                row = rgbe[y, :, ch]
                x = 0
                while x < W:
                    # Find run
                    run_len = 1
                    while x + run_len < W and row[x + run_len] == row[x] and run_len < 127:
                        run_len += 1
                    if run_len > 2:
                        f.write(bytes([run_len + 128, row[x]]))
                        x += run_len
                    else:
                        # Non-run: find non-repeating stretch
                        non_run = 1
                        while x + non_run < W and non_run < 128:
                            if (x + non_run + 1 < W and
                                row[x + non_run] == row[x + non_run + 1]):
                                break
                            non_run += 1
                        f.write(bytes([non_run]))
                        f.write(bytes(row[x:x + non_run]))
                        x += non_run


def resize_hdr(src, dst, target_width=2048):
    print(f'Reading {src}...')
    rgb = read_hdr(src)
    H, W = rgb.shape[:2]
    print(f'Original: {W}x{H}, size={os.path.getsize(src)/1024/1024:.1f}MB')

    # Compute new size (maintain aspect)
    target_height = int(H * target_width / W)
    print(f'Resizing to {target_width}x{target_height}...')

    # Use PIL for high-quality resize (tone-map to 8-bit, resize, restore HDR range)
    # Scale to 0-255, resize, scale back
    max_val = rgb.max()
    if max_val > 0:
        rgb_norm = np.clip(rgb / max_val, 0, 1)
    else:
        rgb_norm = rgb

    img8 = (rgb_norm * 255).astype(np.uint8)
    pil = Image.fromarray(img8, 'RGB')
    pil_r = pil.resize((target_width, target_height), Image.LANCZOS)
    rgb_r = np.array(pil_r).astype(np.float32) / 255.0 * max_val

    print(f'Writing {dst}...')
    write_hdr(dst, rgb_r)
    print(f'Done. Output size: {os.path.getsize(dst)/1024/1024:.1f}MB')


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'static/skyboxes/T_Skybox_13_HybridNoise.HDR'
    dst = sys.argv[2] if len(sys.argv) > 2 else src.replace('.HDR', '_2k.hdr').replace('.hdr', '_2k.hdr')
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
    resize_hdr(src, dst, width)
