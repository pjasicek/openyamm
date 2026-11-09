#!/bin/bash
# textures changed, mesh not: ramps -> export -> everything
G=../claude_shared/gltf_venv/bin/python
$G scripts/tier_dwarf.py 2>&1 | grep -E 'share|RAMPS'
