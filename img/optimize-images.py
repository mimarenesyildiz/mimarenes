#!/usr/bin/env python3
"""
Inner page image optimizer — responsive srcset generator.
Generates 640w, 1280w, 2560w, 3840w versions in both JPG and WebP.

NO 16:9 crop — preserves original aspect ratio.
Only resizes by width; skips if source is smaller than target (no upscale).
"""

import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageFilter
import pillow_avif

# Configuration
WIDTHS = [800, 1280, 1920, 2560, 3840]
MAX_IMAGE_PIXELS = 250_000_000
WEBP_QUALITY = 94
JPG_QUALITY = 95
AVIF_QUALITY = 75
HIGH_DETAIL_MARKERS = ("eskiz", "site")
HIGH_DETAIL_JPG_QUALITY = 97
HIGH_DETAIL_WEBP_QUALITY = 99
HIGH_DETAIL_AVIF_QUALITY = 85

IMG_DIR = Path(__file__).parent

# File extensions to process
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


def get_project_dirs():
    """Discover all project subdirectories in img/."""
    dirs = []
    for item in sorted(IMG_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            dirs.append(item)
    return dirs


def generate_variants(src_path: Path, out_dir: Path):
    """Generate all size variants for a source image."""
    stem = src_path.stem
    is_high_detail = any(marker in stem.lower() for marker in HIGH_DETAIL_MARKERS)
    jpg_quality = HIGH_DETAIL_JPG_QUALITY if is_high_detail else JPG_QUALITY
    webp_quality = HIGH_DETAIL_WEBP_QUALITY if is_high_detail else WEBP_QUALITY
    avif_quality = HIGH_DETAIL_AVIF_QUALITY if is_high_detail else AVIF_QUALITY
    print(f"\n  Processing: {src_path.name}")

    try:
        img = Image.open(src_path)
    except Exception as e:
        print(f"    ⚠ Error opening: {e}")
        return

    orig_w, orig_h = img.size
    print(f"    Original: {orig_w}×{orig_h}")

    # Convert to RGB if needed (for JPG compatibility)
    if img.mode in ("RGBA", "P"):
        img_rgb = img.convert("RGB")
    else:
        img_rgb = img

    for width in WIDTHS:
        # Skip if source is smaller than target (no upscale)
        if width > orig_w:
            print(f"    ⚠ {width}w: skipped (source only {orig_w}px wide)")
            continue

        # Calculate height preserving aspect ratio
        ratio = width / orig_w
        height = int(orig_h * ratio)
        resized = img_rgb.resize((width, height), Image.LANCZOS)
        if is_high_detail:
            resized = resized.filter(ImageFilter.UnsharpMask(radius=0.8, percent=140, threshold=2))

        # Save JPG
        jpg_path = out_dir / f"{stem}-{width}w.jpg"
        jpg_kwargs = {"quality": jpg_quality, "optimize": True}
        if is_high_detail:
            jpg_kwargs["subsampling"] = 0
        resized.save(jpg_path, "JPEG", **jpg_kwargs)
        jpg_size = jpg_path.stat().st_size / 1024

        # Save WebP via cwebp for better compression
        temp_png = out_dir / f"_temp_{stem}-{width}w.png"
        resized.save(temp_png, "PNG")

        webp_path = out_dir / f"{stem}-{width}w.webp"
        subprocess.run(
            ["cwebp", "-q", str(webp_quality), "-m", "6", "-sharp_yuv", str(temp_png), "-o", str(webp_path)],
            capture_output=True,
            check=True,
        )
        webp_size = webp_path.stat().st_size / 1024

        # Save AVIF
        avif_path = out_dir / f"{stem}-{width}w.avif"
        resized.save(avif_path, "AVIF", quality=avif_quality, speed=4)
        avif_size = avif_path.stat().st_size / 1024

        temp_png.unlink()  # Clean up temp

        print(f"    ✓ {width}w: {width}×{height}  JPG={jpg_size:.0f}KB  WebP={webp_size:.0f}KB  AVIF={avif_size:.0f}KB")

    img.close()


def main():
    print("Inner Page Image Optimizer")
    print(f"Breakpoints: {WIDTHS}")
    print(f"Max image pixels: {MAX_IMAGE_PIXELS:,}")
    print(f"JPG quality: {JPG_QUALITY}, WebP quality: {WEBP_QUALITY}")
    print(
        "High-detail profile: "
        f"{HIGH_DETAIL_MARKERS} -> JPG {HIGH_DETAIL_JPG_QUALITY}, WebP {HIGH_DETAIL_WEBP_QUALITY}"
    )

    project_dirs = get_project_dirs()
    print(f"Found {len(project_dirs)} project directories")

    total_processed = 0

    for proj_dir in project_dirs:
        print(f"\n{'='*60}")
        print(f"Project: {proj_dir.name}")

        # Create optimized output directory
        out_dir = proj_dir / "optimized"
        out_dir.mkdir(exist_ok=True)

        # Find all image files in project directory
        image_files = []
        for f in sorted(proj_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                image_files.append(f)

        if not image_files:
            print("  No image files found, skipping.")
            continue

        print(f"  Found {len(image_files)} images")

        for img_file in image_files:
            generate_variants(img_file, out_dir)
            total_processed += 1

    print(f"\n{'='*60}")
    print(f"Done! Processed {total_processed} images across {len(project_dirs)} projects")

    # Summary
    total_size = 0
    for proj_dir in project_dirs:
        opt_dir = proj_dir / "optimized"
        if opt_dir.exists():
            for f in opt_dir.glob("*"):
                if not f.name.startswith("_temp_"):
                    total_size += f.stat().st_size / 1024

    print(f"Total optimized output: {total_size/1024:.1f} MB")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    if len(sys.argv) > 2:
        generate_variants(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        main()
