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

Requires `just` and Python 3.9+. PHP formatting also requires PHP CS Fixer. On macOS:

```sh
brew install just python php-cs-fixer
```

On Ubuntu 24.04+ (compression and local configuration):

```sh
sudo apt update && sudo apt install -y just python3-venv
```

For PHP formatting, also install [PHP CS Fixer](https://cs.symfony.com/doc/installation.html).

```sh
just format               # Format PHP using PSR-12
just test                 # Check formatting without changes
just init                 # Copy the example; fail if local config exists
just compress             # Process the entire project recursively
just compress /srv/images # Or choose a directory, including an external collection
```

The `init` and `compress` recipes call Python scripts in `tools/`.
On its first run, `just compress` automatically downloads Pillow and the HEIC
decoder into a private environment in `tools/.venv-compress` (internet required).
Later runs work offline. ImageMagick and system image codecs are not needed.

GitHub Actions runs `just test` on every push and pull request.
If the check fails, run `just format` locally and include the formatting changes.
CI uses PHP 8.5 and PHP CS Fixer 3.95.27.

Image processing replaces files larger than 1 MB (1,000,000 bytes) with JPGs
of at most 1 MB in the same directory. Smaller files are left unchanged.
It skips `.git` and symbolic links, preserves originals if conversion fails,
and refuses to overwrite another image with the same JPG filename.
Failed conversions are reported and skipped so the batch can finish; the command
exits with status 1 if any conversions failed.
Conversion uses the first frame of animated images, a white background for
transparency, and removes metadata after applying orientation.
It lowers JPEG quality first and reduces image dimensions only when needed to
meet the 1 MB limit.
