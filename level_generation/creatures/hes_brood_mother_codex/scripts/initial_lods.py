"""Initial colour/shadow LODs using the shared exporter, preserving floor contacts."""
import bpy,sys,os,signal
from pathlib import Path
import numpy as np
signal.alarm(900)
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P.parents[2]/'tools'),str(P.parent/'claude_shared/gates')]
from build_actor_lods import generate
from run_gates import Glb,load_meshes
source=P/'work/prepared_lod0.glb';m=load_meshes(Glb(source))[0]
protected=m.rest[m.rest[:,2]<.015].tolist()
generate(source,P/'work/initial_lods.glb','BroodMother',ratios=(.5,.25,.125),max_influences=4,protected_points=protected)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
