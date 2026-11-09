from pathlib import Path
import sys
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import pbr_round3 as pbr
for tier in 'abc':pbr.render('low',tier,f'lod3_low_{tier}',88,3)
