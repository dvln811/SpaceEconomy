"""Pre-decode HDR skybox textures to PNG for fast loading.
Run this whenever skybox HDR files change.

Outputs tone-mapped PNG files that the browser can decode natively (fast).
The shader handles the HDR blending, so we store linear RGB values
scaled to preserve the dynamic range in 16-bit PNG.
"""
import struct
import os
import numpy as np
from PIL import Image

SKYBOX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'skyboxes')
CACHE_DIR = os.path.join(SKYBOX_DIR, 'cached')

def decode_hdr(filepath):
    """Decode RGBE (.hdr) file to float32 RGB array."""
    with open(filepath, 'rb') as f:
        # Read header
        line = f.readline()
        while line.strip():
            line = f.readline()
        # Resolution line
        res_line = f.readline().decode('ascii').strip()
        parts = res_line.split()
        height = int(parts[1])
        width = int(parts[3])
        
        # Read pixel data (run-length encoded RGBE)
        pixels = np.zeros((height, width, 3), dtype=np.float32)
        
        for y in range(height):
            r, g = struct.unpack('BB', f.read(2))
            if r != 2 or g != 2:
                raise ValueError(f"Expected new RLE format at scanline {y}")
            scanline_width = struct.unpack('>H', f.read(2))[0]
            if scanline_width != width:
                raise ValueError(f"Scanline width mismatch")
            
            channels = []
            for ch in range(4):
                channel = []
                while len(channel) < width:
                    byte = struct.unpack('B', f.read(1))[0]
                    if byte > 128:
                        count = byte - 128
                        value = struct.unpack('B', f.read(1))[0]
                        channel.extend([value] * count)
                    else:
                        count = byte
                        channel.extend(struct.unpack(f'{count}B', f.read(count)))
                channels.append(channel)
            
            for x in range(width):
                r, g, b, e = channels[0][x], channels[1][x], channels[2][x], channels[3][x]
                if e == 0:
                    pixels[y, x] = [0, 0, 0]
                else:
                    scale = 2.0 ** (e - 128 - 8)
                    pixels[y, x] = [r * scale, g * scale, b * scale]
    
    return pixels, width, height


def convert_hdr_to_png(hdr_path, png_path):
    """Convert HDR file to 8-bit PNG with linear tone mapping."""
    print(f"  Decoding {os.path.basename(hdr_path)}...")
    pixels, width, height = decode_hdr(hdr_path)
    
    # Linear scale: clamp to reasonable range and map to 0-255
    # Most skybox pixel values are 0-2 range, scale by 128 to fill 0-255
    scale_factor = 128.0
    pixels_u8 = np.clip(pixels * scale_factor, 0, 255).astype(np.uint8)
    
    img = Image.fromarray(pixels_u8, mode='RGB')
    img.save(png_path, format='PNG', compress_level=6)
    
    size_mb = os.path.getsize(png_path) / (1024 * 1024)
    print(f"    -> {os.path.basename(png_path)} ({width}x{height}, {size_mb:.1f} MB)")


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    hdr_files = [f for f in os.listdir(SKYBOX_DIR) if f.endswith('.hdr') and '4k' in f]
    
    if not hdr_files:
        print("No 4k HDR files found in", SKYBOX_DIR)
        return
    
    print(f"Pre-decoding {len(hdr_files)} HDR files to {CACHE_DIR}/")
    
    for hdr_file in sorted(hdr_files):
        hdr_path = os.path.join(SKYBOX_DIR, hdr_file)
        png_file = hdr_file.replace('.hdr', '.png')
        png_path = os.path.join(CACHE_DIR, png_file)
        convert_hdr_to_png(hdr_path, png_path)
    
    print("Done! Client will load .png files for fast skybox display.")


if __name__ == '__main__':
    main()
