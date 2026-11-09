"""Keep the shared clips; provide role aliases for the existing retarget/fit tools."""
from pathlib import Path
import sys
import bpy

P = Path(__file__).resolve().parents[1]
source, output = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()))
for role in ('Standing', 'Walking'):
    action = bpy.data.actions['Carbine_' + role].copy()
    action.name = role
    action.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=str(Path(output).resolve()))
