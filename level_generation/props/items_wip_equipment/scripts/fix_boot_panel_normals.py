"""Correct the two reversed open back panels without moving the painted geometry or its UVs."""
import hashlib
import json
from pathlib import Path
import shutil

import bmesh
import bpy

project = Path(__file__).resolve().parents[1]
path = project / 'work/codex_tex/equipment_7item119.blend'
backup = project / 'work/repairs/equipment_7item119_before_panel_normals.blend'
assert not backup.exists()
shutil.copyfile(path, backup)
bpy.ops.wm.open_mainfile(filepath=str(path))
obj = bpy.data.objects['equipment_7item119']
bm = bmesh.new()
bm.from_mesh(obj.data)
seen, repaired = set(), []
for face in bm.faces:
    if face in seen:
        continue
    stack, faces = [face], []
    seen.add(face)
    while stack:
        current = stack.pop()
        faces.append(current)
        for edge in current.edges:
            for other in edge.link_faces:
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
    before = sum(f.calc_area() * f.calc_center_median().dot(f.normal) / 3 for f in faces)
    if len(faces) > 70 and before < -0.01:
        assert len(faces) in (78, 90)
        bmesh.ops.recalc_face_normals(bm, faces=faces)
        after = sum(f.calc_area() * f.calc_center_median().dot(f.normal) / 3 for f in faces)
        assert after > 0
        repaired.append({'faces': len(faces), 'signed_volume_before': before, 'signed_volume_after': after})
assert len(repaired) == 2
bm.to_mesh(obj.data)
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(path))
receipt = {'components': repaired, 'input_sha256': hashlib.sha256(backup.read_bytes()).hexdigest(),
           'output_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(project / 'review/boot_panel_normals_repair.json').write_text(json.dumps(receipt, indent=2) + '\n')
