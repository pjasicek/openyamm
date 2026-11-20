import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import equipped_reduction as eq
props={n:json.loads((P/f'review/far_props/{n}.json').read_text())for n in ['ForearmBlade','LeafShield']}
for ratio,folder in [(.14,'reduction_v9'),(.18,'reduction_fit'),(.21,'reduction_props')]:
 row=eq.choose('Body',2,ratio,folder);eq.trial(3,f'from_l2_{ratio}',{'Body':row,**props})
