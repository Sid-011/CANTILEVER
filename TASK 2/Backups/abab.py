#!/usr/bin/env python3
"""
ocr_run.py

Simple OCR runner using Tesseract + pytesseract.

Usage examples:
    python ocr_run.py image1.png image2.jpg
    python ocr_run.py --dir images_folder
    python ocr_run.py --tesseract "C:\Users\hd c\Desktop\Tesseract\tesseract.exe" image.png

Requirements:
    pip install pillow pytesseract
    (Make sure tesseract.exe exists at the path below, or pass --tesseract)

This script:
 - Accepts one or more image files OR a directory of images
 - Optionally applies simple preprocessing (grayscale / threshold)
 - Prints a preview and saves OCR output next to each image as .txt
"""

import argparse
import os
import sys
from glob import glob
from PIL import Image, ImageOps
import pytesseract

SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif")

def collect_images_from_dir(directory):
    images = []
    for ext in SUPPORTED_EXTS:
        images.extend(glob(os.path.join(directory, f"*{ext}")))
    return sorted(images)

def preprocess_image(img, do_grayscale=False, do_threshold=False):
    if do_grayscale:
        img = ImageOps.grayscale(img)
    if do_threshold:
        # convert to pure black/white using a simple threshold
        if img.mode != "L":
            img = ImageOps.grayscale(img)
        img = img.point(lambda p: 255 if p > 127 else 0)
    return img

def main():
    parser = argparse.ArgumentParser(description="OCR images with Tesseract (pytesseract wrapper)")
    parser.add_argument("images", nargs="*", help="Image file paths to OCR")
    parser.add_argument("--dir", help="Directory containing images to OCR (alternative to listing files)")
    parser.add_argument(
        "--tesseract",
        default=r"C:\Users\hd c\Desktop\Tesseract\tesseract.exe",
        help=r'Full path to tesseract.exe OR folder containing it (default set to your desktop install).'
    )
    parser.add_argument("--lang", default="eng", help="Tesseract language code (default: eng)")
    parser.add_argument("--psm", default="3", help="Tesseract Page Segmentation Mode (default: 3)")
    parser.add_argument("--grayscale", action="store_true", help="Convert images to grayscale before OCR")
    parser.add_argument("--threshold", action="store_true", help="Apply a simple binary threshold before OCR (useful for noisy text)")
    args = parser.parse_args()

    # Resolve tesseract path: user may have given a folder or the exe directly
    tpath = args.tesseract
    if os.path.isdir(tpath):
        tpath = os.path.join(tpath, "tesseract.exe")
    pytesseract.pytesseract.tesseract_cmd = tpath

    if not os.path.isfile(pytesseract.pytesseract.tesseract_cmd):
        print("ERROR: tesseract.exe not found at:")
        print("  " + pytesseract.pytesseract.tesseract_cmd)
        print("Fix by:")
        print(" - Installing Tesseract and noting the install folder, or")
        print(" - Passing --tesseract with the correct full path to tesseract.exe")
        sys.exit(2)

    # build list of image paths
    image_paths = []
    if args.dir:
        if not os.path.isdir(args.dir):
            print(f"ERROR: directory not found: {args.dir}")
            sys.exit(2)
        image_paths = collect_images_from_dir(args.dir)
    if args.images:
        image_paths.extend(args.images)

    # dedupe and keep only existing supported files
    image_paths = [os.path.abspath(p) for p in dict.fromkeys(image_paths) if os.path.isfile(p) and os.path.splitext(p)[1].lower() in SUPPORTED_EXTS]

    if not image_paths:
        print("No supported image files found. Provide image paths or use --dir.")
        sys.exit(0)

    for img_path in image_paths:
        print(f"\n--- Processing: {img_path} ---")
        try:
            img = Image.open(img_path)
        except Exception as e:
            print(f"Failed to open image: {e}")
            continue

        try:
            img_proc = preprocess_image(img, do_grayscale=args.grayscale, do_threshold=args.threshold)
            custom_config = f'--psm {args.psm}'
            text = pytesseract.image_to_string(img_proc, lang=args.lang, config=custom_config)
        except pytesseract.pytesseract.TesseractError as e:
            print(f"Tesseract error: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error during OCR: {e}")
            continue

        preview = text.strip().replace("\n", " ")[:400]
        print("Preview:", (preview if preview else "[no text found]"))

        out_file = os.path.splitext(img_path)[0] + ".txt"
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved OCR output to: {out_file}")
        except Exception as e:
            print(f"Could not save output to {out_file}: {e}")

    print("\nDone.")

if __name__ == "__main__":
    main()
