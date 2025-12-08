import sys
import os
from PIL import Image

def resize_image(input_path, output_path, width):
    img = Image.open(input_path)
    w_percent = width / float(img.size[0])
    h_size = int(float(img.size[1]) * w_percent)
    img = img.resize((width, h_size), Image.LANCZOS)
    img.save(output_path)
    print(f"✅ Lanczos resize saved to: {output_path}")

def resize_crisp(input_path, output_path, width):
    img = Image.open(input_path)
    w_percent = width / img.size[0]
    h_size = int(img.size[1] * w_percent)
    small = img.resize((width, h_size), Image.NEAREST)
    small.save(output_path)
    print(f"✅ Nearest-neighbor resize saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python 1_resize_image.py <image_path>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_small{ext}"

    # Choose one:
    #resize_image(input_file, output_file, width=100)
    resize_crisp(input_file, output_file, width=400)
