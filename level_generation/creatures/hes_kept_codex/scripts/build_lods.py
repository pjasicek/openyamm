"""Shared LOD builder inside the bounded, immediate-exit Blender runner."""
import sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));import build_actor_lods as B
stem=sys.argv[sys.argv.index('--')+1]
B.generate(P/'export'/f'{stem}_runtime_lod0.glb',P/'export'/f'{stem}_lods.glb','Kept',ratios=(.5,.25,.125),max_influences=8)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
