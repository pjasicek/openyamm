"""Regenerate the final articulated shell around the fitted motions, export, and audit."""
from pathlib import Path
import runpy
import sys
P=Path(__file__).resolve().parents[1]
audit_args = [] if '--full' in sys.argv else ['--shell-only']
sys.path.insert(0,str(P/'scripts'))
for script,args in [('armour_spec_lancer.py',[]),
                    ('shoulder_weights.py',[P/'work/forge_motion.blend',P/'work/forge_weighted.blend']),
                    ('finalize_authoring.py',[]),('audit_authoring.py',audit_args)]:
    print('FINISH_SHELL',script,flush=True)
    sys.argv=[script,'--',*map(str,args)]
    runpy.run_path(str(P/'scripts'/script),run_name='__main__')
