#!/bin/bash
# System python (yaml) + the shared gltf venv's pure-python packages (pygltflib): convert_abc_model.py needs both.
PYTHONPATH="/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/lib/python3.14/site-packages" exec python3 "$@"
