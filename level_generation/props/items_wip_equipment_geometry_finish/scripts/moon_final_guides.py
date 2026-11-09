"""Keep exact final-assembly guides separate from the accepted textured scene."""
import sys
from pathlib import Path
import bpy
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import codex_texture as texture
bpy.ops.wm.open_mainfile(filepath=str(P/'work/codex_tex/geometryfinish_7item348_pbr.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/codex_tex/equipment_7item348.blend'))
texture.guides('equipment_7item348')
