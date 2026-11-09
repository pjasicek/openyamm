#!/usr/bin/env python3
"""Builder 2: compose.py, except that a LOD whose shell was carved away completely (swamp pads: every face over a
sky gap or facing down) gets no Shell primitive instead of an empty one. Otherwise identical (runs compose.py).
Usage: b2_compose.py <id>"""
import os, runpy, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb

_add = glb.Model.add_primitive


def add_primitive(self, mesh, material, positions, normals, uvs, colours, indices):
    if len(indices) == 0:
        print(f'B2_COMPOSE mesh {mesh}: no shell faces left, no Shell primitive')
        return None
    return _add(self, mesh, material, positions, normals, uvs, colours, indices)


glb.Model.add_primitive = add_primitive
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compose.py'), run_name='__main__')
