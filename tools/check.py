#!/usr/bin/env python3
"""Runs every check:  python tools/check.py

1. Unit tests of the renderer-independent core (no Blender needed).
2. Profile parity: builds preview and final in Blender and compares camera and pivots.
3. Locked sequence: compares every object's transform and colour through 1:05 with the
   recorded reference of the approved film.
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from render import find_blender  # noqa: E402


def main():
    suite = unittest.defaultTestLoader.discover(os.path.join(ROOT, "tests"), pattern="test_*.py")
    if not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():
        sys.exit(1)

    blender = find_blender(os.environ.get("BLENDER"))
    for script in ("blender_parity.py", "blender_locked.py"):
        command = [blender, "-b", "--factory-startup", "--python-exit-code", "1",
                   "--python", os.path.join(ROOT, "tests", script)]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
        lines = [line for line in result.stdout.splitlines() if line.startswith("[pd]")]
        # A named failure is reported as such; anything else gets Blender's raw output.
        failed = result.returncode != 0
        print("\n".join(lines) if lines and (not failed or any("FAIL" in line for line in lines)) else result.stdout[-4000:])
        if failed:
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
