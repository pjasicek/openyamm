#!/usr/bin/env python3
"""Converts every Tasar Academy prop this project builds (props_table.built_props(); each book variant is its own
conversion of the book) with the Anskram Keep's convert step (tools/mm9_import_discovery/convert_abc_model.py through the isle's
venv: rigid export, else full for deforming models; LOD 0 in work/raw/<prop>/<prop>.glb, each native ABC LOD n in
work/raw/<prop>/lod<n>/; MM9 skin as PNG). Usage: convert_all.py [prop ...]"""
import sys

import anskram
import props_table

convert = anskram.load('convert_all').convert


def main():
    # the posed props are converted by hand in full mode (README): never by default
    props = sys.argv[1:] or [p for p in props_table.built_props() if p not in props_table.POSES]
    for prop in props:
        convert(prop)


if __name__ == '__main__':
    main()
