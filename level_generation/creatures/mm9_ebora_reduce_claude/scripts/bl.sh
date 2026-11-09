#!/usr/bin/env bash
# one Blender job under the shared memory scope: bl.sh <script.py> [-- args]   (env passes through)
exec systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 /snap/bin/blender -b --factory-startup --threads 4 -P "$@"
