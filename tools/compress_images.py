#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import venv


LIMIT = 1_000_000
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tif', '.tiff', '.heic', '.heif', '.avif'}


def bootstrap():
    """Install bundled codecs in a private environment on the first run."""
    environment = Path(__file__).resolve().parent / '.venv-compress'
    if Path(sys.prefix) == environment:
        return
    if sys.version_info < (3, 9):
        raise SystemExit('Compression requires Python 3.9 or newer.')
    requirements = Path(__file__).with_name('compress-requirements.txt')
    installed = environment / '.requirements'
    python = environment / 'bin' / 'python'
    try:
        if not python.exists() or not installed.exists() or installed.read_bytes() != requirements.read_bytes():
            print('Installing image codecs (first run only)...', flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
            subprocess.run([
                str(python), '-m', 'pip', 'install', '--quiet', '--disable-pip-version-check', '--no-cache-dir',
                '--only-binary=:all:', '-r', str(requirements),
            ], check=True)
            installed.write_bytes(requirements.read_bytes())
        os.execv(str(python), [str(python), str(Path(__file__).resolve()), *sys.argv[1:]])
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'Could not set up image codecs: {error}\n'
                         'On Ubuntu, install python3-venv. The first run needs internet access.') from None


def compress_image(source, output, limit=LIMIT):
    from PIL import Image, ImageOps

    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened)
        if 'A' in image.getbands() or 'transparency' in image.info:
            rgba = image.convert('RGBA')
            rgb = Image.new('RGB', image.size, 'white')
            rgb.paste(rgba, mask=rgba.getchannel('A'))
        else:
            rgb = image.convert('RGB')
    rgb.info.clear()
    while True:
        for quality in (85, 75, 65, 55):
            rgb.save(output, 'JPEG', quality=quality, optimize=True, progressive=True)
            size = output.stat().st_size
            if 0 < size <= limit:
                return
        if rgb.size == (1, 1):
            raise ValueError('Could not compress below the size limit')
        scale = min(0.9, (limit / size) ** 0.5 * 0.95)
        width, height = rgb.size
        rgb = rgb.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.Resampling.LANCZOS)


def main():
    parser = argparse.ArgumentParser(description='Compress images larger than 1 MB to JPG in place.')
    parser.add_argument('directory', nargs='?', default='.')
    args = parser.parse_args()
    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        parser.error(f'Not a directory: {root}')
    bootstrap()
    from PIL import Image
    from pillow_heif import register_heif_opener

    register_heif_opener(thumbnails=False)
    converted = failed = 0
    for parent, directories, files in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in {'.git', '.venv-compress'})
        for name in sorted(files):
            source = Path(parent) / name
            if source.is_symlink() or source.suffix.lower() not in EXTENSIONS or name.startswith('.snootberg-'):
                continue
            temporary = None
            try:
                original = source.stat()
                if original.st_size <= LIMIT:
                    continue
                target = source.with_suffix('.jpg')
                same_file = target.exists() and source.samefile(target)
                if target.is_symlink() or (target.exists() and not same_file):
                    raise ValueError(f'Refusing to overwrite existing image: {target}')
                with tempfile.NamedTemporaryFile(dir=source.parent, prefix='.snootberg-', suffix='.jpg', delete=False) as output:
                    temporary = Path(output.name)
                compress_image(source, temporary)
                temporary.chmod(stat.S_IMODE(original.st_mode))
                size = temporary.stat().st_size
                temporary.replace(target)
                if not same_file:
                    source.unlink()
                converted += 1
                print(f'{source} -> {target} ({original.st_size} -> {size} bytes)')
            except (OSError, ValueError, SyntaxError, EOFError, RuntimeError, Image.DecompressionBombError) as error:
                failed += 1
                print(f'Failed: {source}; original preserved. {error}', file=sys.stderr)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
    print(f'Converted {converted} image(s); failed {failed}.')
    return int(failed > 0)


if __name__ == '__main__':
    sys.exit(main())
