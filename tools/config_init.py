#!/usr/bin/env python3
from pathlib import Path

target = Path('config.local.php')
with target.open('xb') as output:
    output.write(Path('config.example.php').read_bytes())
print(f'Created {target}; set collection to an absolute directory path.')
