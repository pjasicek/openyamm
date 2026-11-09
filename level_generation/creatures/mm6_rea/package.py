"""Package single-palette native actor."""
import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(ROOT.parent/'mm6_peasants/package_family.py'),'rea'],check=True)
p=ROOT/'manifest.json';m=json.loads(p.read_text());m['recolor_model']='exact_base_bypass_v1';m['recolor']={'model':'exact_base_bypass_v1','operation':'Single native palette; no recoloring; preserve base RGBA exactly.'};p.write_text(json.dumps(m,indent=2)+'\n')
