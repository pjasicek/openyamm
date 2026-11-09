import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import pbr_round3 as p
p.render("low","a","pbr_low_a",views=[0,1])
