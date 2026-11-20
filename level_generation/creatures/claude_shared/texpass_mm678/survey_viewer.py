#!/usr/bin/env python3
"""Throwaway per-skin review viewer of an installed GLB (ramps baked per variant, as the engine applies them), for
identifying models and before-state shots. Reuses mm7_m210_claude/scripts/viewer.py with its paths redirected.
Usage: survey_viewer.py <installed.glb> [title]   -> survey/<stem>/review/viewer/ (run_creature_review.py needs a project directly under creatures/; see ../../mm7_texpass_survey_claude)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'mm7_m210_claude/scripts'))
import viewer as V  # noqa: E402

glb = Path(sys.argv[1]).resolve()
project = HERE / 'survey' / glb.stem
V.P = project
V.VIEWER = project / 'review/viewer'
V.CONFIG = {'build': [{'out': str(glb)}],
            'viewer': {'title': sys.argv[2] if len(sys.argv) > 2 else glb.stem, 'subtitle': 'Installed GLB survey',
                       'labels': ['installed'], 'revision': 'survey-20261101', 'default_clip': 'Standing',
                       'provenance': 'installed'}}
V.main()
