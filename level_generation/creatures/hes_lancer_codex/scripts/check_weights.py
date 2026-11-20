from pathlib import Path
import runpy
import sys
P=Path(__file__).resolve().parents[1]
for script,args in [('shoulder_weights.py',[P/'work/forge_motion.blend',P/'work/forge_weighted.blend']),
                    ('gates.py',[P/'work/forge_weighted.blend','forge_weights','Forge_Attack'])]:
    sys.argv=[script,'--',*map(str,args)]
    runpy.run_path(str(P/'scripts'/script),run_name='__main__')
