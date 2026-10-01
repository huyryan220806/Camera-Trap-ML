"""Check the CPU environment required by the implemented week-one tools."""
import importlib.metadata
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    print(f'Python {platform.python_version()} | {sys.executable}')
    if sys.version_info[:2] != (3, 12):
        errors.append('Python 3.12 is required by the tested environment.')
    for line in (ROOT / 'requirements.txt').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        name, expected = line.split('==')
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = 'not installed'
        print(f'{name}: {actual} (expected {expected})')
        if actual != expected:
            errors.append(f'{name}: install the version pinned in requirements.txt')
    for file in ['data/processed/v1/class_map.json', 'contracts/inference_result.schema.json']:
        if not (ROOT / file).is_file():
            errors.append(f'Missing repository file: {file}')
    for error in errors:
        print('ERROR:', error)
    if errors:
        return 1
    print('Week-one CPU environment OK. GPU, deep-learning runtime and real inference are not checked.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
