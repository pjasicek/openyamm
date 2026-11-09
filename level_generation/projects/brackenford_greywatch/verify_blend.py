"""Run with blender --background SOURCE.blend --python this_file; read-only standalone source check."""
import json
import sys
import bpy
from collections import Counter
from pathlib import Path

scenes=[s for s in bpy.data.scenes if s.get('levelgen_project')=='brackenford_greywatch']
assert len(scenes)==1, [s.name for s in bpy.data.scenes]
assert len(bpy.data.scenes)==1
assert not bpy.data.libraries
scene=scenes[0]
counts=Counter(o.get('levelgen_kind','unspecified') for o in scene.objects)
for image in bpy.data.images:
    if image.source=='FILE':assert image.packed_file or image.packed_files, image.name
if counts['bmodel']:
    source=Path(bpy.data.filepath).parent
    semantic=json.loads((source/'lg01.semantic.json').read_text())
    decorations=json.loads((source/'lg01.decorations.json').read_text())
    assert sum(counts[k] for k in ['bmodel','chest_target','obelisk','well','fountain'])==len(semantic['bmodels'])
    assert counts['decoration_preview']==len(decorations['records'])
else:
    assert counts['mechanism']==8 and counts['decoration_preview']==34 and counts['furnishing']==6
if '--finalize' in sys.argv:
    # libraries.write isolates the authored scene from the driver's other MCP scenes. Save this
    # independently loaded scene as a regular main file with this process's default workspace.
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True,relative_remap=False)
print(json.dumps(dict(file=Path(bpy.data.filepath).name,scene=scene.name,objects=len(scene.objects),kinds=counts,
                     linked_libraries=0,packed_file_images=True,status='pass')))
