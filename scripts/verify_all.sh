#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

python3 -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
node --version >/dev/null

lake build
lake env leanchecker Hcp001.Basic
lake exe hcp001_verify

python3 evidence/verify_z43_boundary.py
python3 evidence/verify_z2_direct.py
python3 evidence/verify_z3_direct.py
python3 evidence/verify_z3_direct_independent.py
node evidence/verify_radius2_and_directed3.js

(cd evidence && shasum -a 256 -c MANIFEST.sha256)
