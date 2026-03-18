#!/usr/bin/env python3
"""
16:9 center-crop + responsive srcset generator for homepage images.
Generates 800w, 1280w, 1920w, 2560w versions in both JPG and WebP.

Auto-scans all .png and .jpg files in the anasayfa/ directory,
excluding enesyildiz.png (profile photo) and .mp4 files.
"""

import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageFilter
import pillow_avif

# Configuration
TARGET_RATIO = 16 / 9  # 1.7778
WIDTHS = [800, 1280, 1920, 2560]
JPG_QUALITY = 95
WEBP_QUALITY = 94
AVIF_QUALITY = 75
HIGH_DETAIL_MARKERS = ("eskiz", "site")
HIGH_DETAIL_JPG_QUALITY = 97
HIGH_DETAIL_WEBP_QUALITY = 99
HIGH_DETAIL_AVIF_QUALITY = 85
HIGH_DETAIL_WEBP_LOSSLESS = False

SRC_DIR = Path(__file__).parent
OUT_DIR = SRC_DIR / "optimized"
OUT_DIR.mkdir(exist_ok=True)

# Excluded files
EXCLUDED = {"enesyildiz.png"}


def discover_sources():
    """Auto-discover all .png and .jpg files in the source directory."""
    sources = []
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        for f in sorted(SRC_DIR.glob(ext)):
            if f.name.lower() in EXCLUDED:
                continue
            sources.append(f.name)
    return sources


def crop_to_16_9(img: Image.Image) -> Image.Image:
    """Center-crop image to exactly 16:9 aspect ratio."""
    w, h = img.size
    current_ratio = w / h

    if current_ratio > TARGET_RATIO:
        # Too wide → crop sides
        new_w = int(h * TARGET_RATIO)
        left = (w - new_w) // 2
        return img.crop((left, 0, left + new_w, h))
    elif current_ratio < TARGET_RATIO:
        # Too tall → crop top/bottom
        new_h = int(w / TARGET_RATIO)
        top = (h - new_h) // 2
        return img.crop((0, top, w, top + new_h))
    else:
        return img  # Already 16:9


def generate_variants(src_filename: str):
    """Generate all size variants for a source image."""
    src_path = SRC_DIR / src_filename
    stem = src_path.stem  # e.g. "seyir-kulesi" or "seyir-kulesi-eskiz"
    is_high_detail = any(marker in stem.lower() for marker in HIGH_DETAIL_MARKERS)
    jpg_quality = HIGH_DETAIL_JPG_QUALITY if is_high_detail else JPG_QUALITY
    webp_quality = HIGH_DETAIL_WEBP_QUALITY if is_high_detail else WEBP_QUALITY
    avif_quality = HIGH_DETAIL_AVIF_QUALITY if is_high_detail else AVIF_QUALITY

    print(f"\n{'='*60}")
    print(f"Processing: {src_filename}")
    if is_high_detail:
        print(f"  Profile:  high-detail (JPG {jpg_quality}, WebP {webp_quality})")
    else:
        print(f"  Profile:  standard (JPG {jpg_quality}, WebP {webp_quality})")

    img = Image.open(src_path)
    print(f"  Original: {img.size[0]}×{img.size[1]} (ratio {img.size[0]/img.size[1]:.3f})")

    # Step 1: Crop to 16:9
    cropped = crop_to_16_9(img)
    print(f"  Cropped:  {cropped.size[0]}×{cropped.size[1]} (ratio {cropped.size[0]/cropped.size[1]:.4f})")

    # Convert to RGB if needed (for JPG compatibility)
    if cropped.mode in ("RGBA", "P"):
        cropped = cropped.convert("RGB")

    for width in WIDTHS:
        # Skip if target width is larger than cropped source
        if width > cropped.size[0]:
            print(f"  ⚠ {width}w: skipped (source only {cropped.size[0]}px wide)")
            continue

        # Calculate height maintaining 16:9
        height = int(width * 9 / 16)
        resized = cropped.resize((width, height), Image.LANCZOS)
        if is_high_detail:
            # Add a light post-resize sharpen pass for linework and UI screenshots.
            resized = resized.filter(ImageFilter.UnsharpMask(radius=0.8, percent=140, threshold=2))

        # Preserve edges on sketch/UI imagery by disabling chroma subsampling there.
        jpg_path = OUT_DIR / f"{stem}-{width}w.jpg"
        jpg_kwargs = {"quality": jpg_quality, "optimize": True}
        if is_high_detail:
            jpg_kwargs["subsampling"] = 0
        resized.save(jpg_path, "JPEG", **jpg_kwargs)
        jpg_size = jpg_path.stat().st_size / 1024

        # Save WebP via cwebp for better compression
        # First save a temp PNG for cwebp input
        temp_png = OUT_DIR / f"_temp_{stem}-{width}w.png"
        resized.save(temp_png, "PNG")

        webp_path = OUT_DIR / f"{stem}-{width}w.webp"
        webp_cmd = ["cwebp", "-m", "6", "-sharp_yuv"]
        if is_high_detail and HIGH_DETAIL_WEBP_LOSSLESS:
            webp_cmd.extend(["-lossless", "-z", "9"])
        else:
            webp_cmd.extend(["-q", str(webp_quality)])
        webp_cmd.extend([str(temp_png), "-o", str(webp_path)])
        subprocess.run(webp_cmd, capture_output=True, check=True)
        webp_size = webp_path.stat().st_size / 1024

        # Save AVIF
        avif_path = OUT_DIR / f"{stem}-{width}w.avif"
        resized.save(avif_path, "AVIF", quality=avif_quality, speed=4)
        avif_size = avif_path.stat().st_size / 1024

        temp_png.unlink()  # Clean up temp

        print(f"  ✓ {width}w: {width}×{height}  JPG={jpg_size:.0f}KB  WebP={webp_size:.0f}KB  AVIF={avif_size:.0f}KB")

    img.close()


def main():
    sources = discover_sources()

    print("16:9 Responsive Srcset Generator")
    print(f"Breakpoints: {WIDTHS}")
    print(f"JPG quality: {JPG_QUALITY}, WebP quality: {WEBP_QUALITY}")
    print(
        "High-detail profile: "
        f"{HIGH_DETAIL_MARKERS} -> JPG {HIGH_DETAIL_JPG_QUALITY}, "
        f"WebP {'lossless' if HIGH_DETAIL_WEBP_LOSSLESS else HIGH_DETAIL_WEBP_QUALITY}"
    )
    print(f"Found {len(sources)} source images")

    processed = 0
    skipped = 0

    for src in sources:
        if not (SRC_DIR / src).exists():
            print(f"⚠ Not found: {src}")
            skipped += 1
            continue
        generate_variants(src)
        processed += 1

    print(f"\n{'='*60}")
    print(f"Done! Processed {processed} images, skipped {skipped}")
    print(f"\nGenerated files in {OUT_DIR}:")

    total_size = 0
    for f in sorted(OUT_DIR.glob("*")):
        if f.name.startswith("_temp_"):
            continue
        size_kb = f.stat().st_size / 1024
        total_size += size_kb
        print(f"  {f.name:50s} {size_kb:>7.0f} KB")

    print(f"\n  Total: {total_size/1024:.1f} MB")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_variants(sys.argv[1])
    else:
        main()
