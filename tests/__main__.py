"""Run offline discovery, failing rather than succeeding with zero tests."""
from pathlib import Path
import sys
import unittest


def main():
    root = Path(__file__).resolve().parent.parent
    suite = unittest.defaultTestLoader.discover(str(root / 'tests'), top_level_dir=str(root))
    if suite.countTestCases() == 0:
        print('ERROR: no tests discovered', file=sys.stderr)
        return 1
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
