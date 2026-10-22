#!/usr/bin/env python3
"""Optimize a supplied, rights-cleared local still image. Requires Pillow locally."""
import argparse
from pathlib import Path
from PIL import Image, ImageOps

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('destination', type=Path)
args = parser.parse_args()
if args.destination.suffix != '.webp' or args.destination.exists():
    parser.error('Choose a new .webp destination; existing files are never overwritten')
with Image.open(args.source) as original:
    if getattr(original, 'n_frames', 1) != 1:
        parser.error('Use a still image')
    image = ImageOps.exif_transpose(original).convert('RGB')
    image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    # A fresh pixel buffer strips EXIF (including GPS), XMP, and other embedded metadata.
    clean = Image.new('RGB', image.size)
    clean.paste(image)
    from io import BytesIO
    for quality in (82, 76, 68, 60):
        output = BytesIO()
        clean.save(output, format='WEBP', quality=quality, method=6)
        if output.tell() <= 400_000:
            args.destination.parent.mkdir(parents=True, exist_ok=True)
            with args.destination.open('xb') as target:
                target.write(output.getvalue())
            print(f'{args.destination}: {clean.width}×{clean.height}, {output.tell():,} bytes, quality {quality}')
            break
    else:
        parser.error('Still over 400KB; reduce dimensions and review quality before trying again')
