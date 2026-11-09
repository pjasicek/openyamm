import sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from reduce_natf import trial
for level,ratios in [(2,[.21]),(3,[.1])]:
 trial('Body',level,1)
 for ratio in ratios:trial('Body',level,ratio)
for part in ['ForearmBlade','LeafShield']:
 for level,ratios in [(0,[.9,.75,.6]),(1,[.35,.25]),(2,[.18,.12]),(3,[.08,.05])]:
  trial(part,level,1)
  for ratio in ratios:trial(part,level,ratio)
