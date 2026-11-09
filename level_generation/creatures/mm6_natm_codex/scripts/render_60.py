import sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from reduction_render import render
render(P/'work/reduced_baked_60.blend',P/'review/reduction/probe60',P/'work/reduction/lod0_60')
