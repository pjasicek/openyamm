#!/bin/bash
# Floor passes (project folder): floor.sh <in> <out>. Pass 1 every living clip + Death/Dead, pass 2 Death2/Dead2, pass 3 Death3 (re-grounds Dead, idempotent).
# Intermediates: work/_floor1.glb, work/_floor2.glb (overwritten each run).
G=../claude_shared/gltf_venv/bin/python; L=../claude_shared/floor
$G -W ignore $L/floor_fix.py $1 work/_floor1.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -1
$G -W ignore $L/floor_fix.py work/_floor1.glb work/_floor2.glb --ground-death Death2 Dead2 2>&1 | tail -1
$G -W ignore $L/floor_fix.py work/_floor2.glb $2 --ground-death Death3 Dead 2>&1 | tail -1
