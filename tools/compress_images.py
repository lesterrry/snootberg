#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

if shutil.which('magick') is None:
    raise SystemExit('ImageMagick is required: install it with brew install imagemagick')

parser = argparse.ArgumentParser(description='Compress images larger than 1 MB to JPG in place.')
parser.add_argument('directory', nargs='?', default='.')
args = parser.parse_args()
root = Path(args.directory).resolve(strict=True)
if not root.is_dir():
    raise SystemExit(f'Not a directory: {root}')

limit = 1_000_000
extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff', '.heic', '.avif'}
converted = 0
for parent, directories, files in os.walk(root, followlinks=False):
    directories[:] = sorted(name for name in directories if name != '.git')
    for name in sorted(files):
        source = Path(parent) / name
        if source.is_symlink() or source.suffix.lower() not in extensions:
            continue
        original = source.stat()
        if original.st_size <= limit:
            continue

        target = source.with_suffix('.jpg')
        same_file = target.exists() and source.samefile(target)
        if target.is_symlink() or (target.exists() and not same_file):
            raise SystemExit(f'Refusing to overwrite existing file: {target}')

        with tempfile.NamedTemporaryFile(dir=source.parent, prefix='.snootberg-', suffix='.jpg', delete=False) as output:
            temporary = Path(output.name)
        try:
            subprocess.run([
                'magick', f'{source}[0]', '-auto-orient', '-strip',
                '-background', 'white', '-alpha', 'remove', '-alpha', 'off',
                '-quality', '85', '-define', f'jpeg:extent={limit}B', str(temporary),
            ], check=True)
            size = temporary.stat().st_size
            if not 0 < size <= limit:
                raise SystemExit(f'Could not compress below 1 MB; original preserved: {source}')
            temporary.chmod(stat.S_IMODE(original.st_mode))
            temporary.replace(target)
            if not same_file:
                source.unlink()
            converted += 1
            print(f'{source} -> {target} ({original.st_size} -> {size} bytes)')
        finally:
            temporary.unlink(missing_ok=True)
print(f'Converted {converted} image(s).')
