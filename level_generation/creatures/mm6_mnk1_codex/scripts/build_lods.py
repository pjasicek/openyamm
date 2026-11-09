"""Fit the LOD chain to the measured actor switch sizes; preserve LOD0 bytes."""
import bpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'));import build_actor_lods as lods
bpy.ops.wm.read_factory_settings(use_empty=True)
lods.generate(p/'export/mm6_mnk1_runtime_lod0.glb',p/'export/mm6_mnk1_lods.glb','Monk',ratios=(.75,.7,.65))
