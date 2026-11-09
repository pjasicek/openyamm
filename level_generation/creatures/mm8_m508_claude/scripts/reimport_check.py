from pathlib import Path
import sys,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared/gates'))
from test_gates import blender_parity
result=blender_parity(p/'export/mm8_m508.glb')
(p/'work/reimport_parity.json').write_text(json.dumps(result,indent=2)+'\n')
