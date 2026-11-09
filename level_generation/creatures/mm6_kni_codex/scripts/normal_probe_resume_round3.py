import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import bake_lod_normals_round3 as n
import pbr_round3 as p
n.bake(3)
p.render("low","a","normal_l1",550,1,views=[0,2])
