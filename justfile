default:
    @just --list

# Format PHP files using PSR-12.
format:
    php-cs-fixer fix . --rules=@PSR12 --using-cache=no

# Check PHP formatting without modifying files.
test:
    php-cs-fixer fix . --rules=@PSR12 --using-cache=no --dry-run --diff

# Create installation configuration without overwriting an existing file.
init:
    python3 tools/config_init.py

# Replace images larger than 1 MB with compressed JPGs (default: entire project).
compress $directory='.':
    python3 tools/compress_images.py "$directory"
