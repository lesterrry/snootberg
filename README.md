# 🐕 random dog images!!!
‼️ Please refer to [CONTRIBUTING.md](https://github.com/lesterrry/snootberg/blob/master/CONTRIBUTING.md) before creating a PR

## Installation configuration

By default, images are served from the bundled `collection` directory.
To use another directory on this installation:

```sh
just init
```

Edit `collection` in `config.local.php` to an absolute filesystem path.
The directory must exist, be readable by PHP, and contain images matching
the formats listed in `index.php`.

`config.local.php` is ignored by Git, so installation settings stay local.
Both web and CLI execution use this configuration. Removing the file restores
the default directory.

## Development commands

Requires `just`, Python 3.8+, PHP CS Fixer, and ImageMagick. On macOS:

```sh
brew install just python php-cs-fixer imagemagick
```

```sh
just format               # Format PHP using PSR-12
just test                 # Check formatting without changes
just init                 # Copy the example; fail if local config exists
just compress             # Process the entire project recursively
just compress /srv/images # Or choose a directory, including an external collection
```

The `init` and `compress` recipes call Python scripts in `tools/`.

GitHub Actions runs `just test` on every push and pull request.
If the check fails, run `just format` locally and include the formatting changes.
CI uses PHP 8.5 and PHP CS Fixer 3.95.27.

Image processing replaces files larger than 1 MB (1,000,000 bytes) with JPGs
of at most 1 MB in the same directory. Smaller files are left unchanged.
It skips `.git` and symbolic links, preserves originals if conversion fails,
and refuses to overwrite another image with the same JPG filename.
Conversion uses the first frame of animated images, a white background for
transparency, and removes metadata after applying orientation.
