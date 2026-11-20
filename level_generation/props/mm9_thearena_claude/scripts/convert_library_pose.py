#!/usr/bin/env python3
"""Sturmford City's convert_library_pose.py (tools/mm9_import_discovery/convert_abc_model.py with an MM9 animation
library's animation added to the model first), run from here: its convert step (sturmford.load('convert_all')) calls
<this project>/scripts/convert_library_pose.py. Environment and arguments as that script's."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parents[2] / 'mm9_sturmfordcity_claude/scripts/convert_library_pose.py'),
               run_name='__main__')
