from pathlib import Path
import os
import random
import stat
import subprocess
import sys
import tempfile
import unittest

from PIL import Image
from pillow_heif import register_heif_opener

from compress_images import compress_image, LIMIT


SCRIPT = Path(__file__).with_name('compress_images.py')
register_heif_opener(thumbnails=False)


class CompressionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.images = self.root / 'images'
        self.images.mkdir()

    def image(self, name, image=None, **options):
        path = self.images / name
        if image is None:
            image = Image.frombytes('RGB', (512, 512), random.Random(0).randbytes(512 * 512 * 3))
        image.save(path, **options)
        # Trailing padding exercises the CLI's input-size threshold without huge fixtures.
        with path.open('ab') as output:
            output.write(b'\0' * max(0, LIMIT + 1 - path.stat().st_size))
        return path

    def compress(self):
        # ImageMagick and other external image tools are deliberately unavailable.
        env = dict(os.environ, PATH='/nonexistent')
        return subprocess.run([sys.executable, str(SCRIPT), str(self.images)],
                              env=env, capture_output=True, text=True)

    def test_supported_formats_produce_valid_jpegs_under_limit(self):
        for extension in ('png', 'jpg', 'webp', 'bmp', 'tiff', 'heic', 'avif'):
            with self.subTest(extension=extension):
                source = self.image(f'photo_{extension}.{extension}')
                result = self.compress()
                self.assertEqual(result.returncode, 0, result.stderr)
                target = source.with_suffix('.jpg')
                self.assertLessEqual(target.stat().st_size, LIMIT)
                with Image.open(target) as image:
                    self.assertEqual(image.format, 'JPEG')
                    self.assertEqual(image.size, (512, 512))
                    image.load()
                if source != target:
                    self.assertFalse(source.exists())

    def test_corrupt_image_is_preserved_and_batch_continues(self):
        before = self.image('a_before.png')
        bad = self.images / 'b_bad.heic'
        bad.write_bytes(b'x' * (LIMIT + 1))
        after = self.image('c_after.png')
        result = self.compress()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(bad.read_bytes(), b'x' * (LIMIT + 1))
        self.assertFalse(bad.with_suffix('.jpg').exists())
        for source in (before, after):
            self.assertFalse(source.exists())
            self.assertLessEqual(source.with_suffix('.jpg').stat().st_size, LIMIT)
        self.assertFalse(list(self.images.glob('.snootberg-*')))
        self.assertIn('Converted 2 image(s); failed 1.', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_orientation_metadata_and_permissions(self):
        exif = Image.Exif()
        exif[274] = 6
        exif[315] = 'private author'
        source = self.image('photo.jpg', Image.new('RGB', (160, 80), 'red'), exif=exif)
        source.chmod(0o640)
        result = self.compress()
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(source) as image:
            self.assertEqual(image.size, (80, 160))
            self.assertFalse(image.getexif())
        self.assertEqual(stat.S_IMODE(source.stat().st_mode), 0o640)

    def test_transparency_and_first_animation_frame(self):
        rgba = Image.new('RGBA', (80, 80), (255, 0, 0, 0))
        rgba.paste((255, 0, 0, 255), (40, 0, 80, 80))
        png = self.image('transparent.png', rgba)
        gif = self.image('animated.gif', Image.new('RGB', (80, 80), 'red'),
                         save_all=True, append_images=[Image.new('RGB', (80, 80), 'blue')])
        result = self.compress()
        self.assertEqual(result.returncode, 0, result.stderr)
        with Image.open(png.with_suffix('.jpg')) as image:
            self.assertTrue(all(channel > 245 for channel in image.getpixel((10, 40))))
        with Image.open(gif.with_suffix('.jpg')) as image:
            red, green, blue = image.getpixel((40, 40))
            self.assertGreater(red, 240)
            self.assertLess(blue, 10)

    def test_dimensions_reduce_when_quality_alone_is_insufficient(self):
        source = self.image('noise.png')
        output = self.root / 'small.jpg'
        compress_image(source, output, limit=2000)
        self.assertLessEqual(output.stat().st_size, 2000)
        with Image.open(output) as image:
            self.assertLess(image.width, 512)
            self.assertEqual(image.width, image.height)
            image.load()

    def test_existing_target_is_never_overwritten(self):
        original = self.image('photo.png')
        target = self.images / 'photo.jpg'
        target.write_bytes(b'existing')
        result = self.compress()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(target.read_bytes(), b'existing')
        self.assertEqual(original.stat().st_size, LIMIT + 1)

    def test_small_files_symlinks_and_internal_directories_are_skipped(self):
        small = self.images / 'small.png'
        small.write_bytes(b'unchanged')
        external = self.root / 'external.png'
        external.write_bytes(b'x' * (LIMIT + 1))
        (self.images / 'link.png').symlink_to(external)
        for directory in ('.git', '.venv-compress'):
            internal = self.images / directory
            internal.mkdir()
            (internal / 'image.png').write_bytes(external.read_bytes())
        result = self.compress()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Converted 0 image(s); failed 0.', result.stdout)
        self.assertEqual(small.read_bytes(), b'unchanged')
        self.assertEqual(external.stat().st_size, LIMIT + 1)
        self.assertTrue((self.images / 'link.png').is_symlink())


if __name__ == '__main__':
    unittest.main()
