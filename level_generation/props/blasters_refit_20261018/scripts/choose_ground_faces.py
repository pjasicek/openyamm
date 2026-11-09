"""Rest the MM6 rifle and shotgun with their icon's indicator/receiver face visible."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_models import settle

P = Path(__file__).resolve().parents[1]


def main():
    receipt_path = P / 'receipts/ground_faces.json'
    receipts = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    for icon in sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['raygun2', 'blastsg']:
        assert icon in ['raygun2', 'blastsg']
        path = P / 'work/meshy' / f'{icon}_export.glb'
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
        obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        obj.matrix_world = Matrix.Rotation(math.pi, 4, 'Y') @ obj.matrix_world
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        if obj.data.has_custom_normals:
            obj.data.normals_split_custom_set([(0, 0, 0)] * len(obj.data.loops))
        angle = settle(obj)
        lo = Vector([min(v.co[a] for v in obj.data.vertices) for a in range(3)])
        hi = Vector([max(v.co[a] for v in obj.data.vertices) for a in range(3)])
        span = max(hi.x-lo.x, hi.y-lo.y)
        for v in obj.data.vertices:
            v.co = (v.co-Vector(((lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z)))/span
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        assert abs(min(v.co.z for v in obj.data.vertices)) < 1e-6
        bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True, export_yup=True)
        receipts[icon] = {'icon_face_up': True, 'support_rotation_degrees': angle}
    receipt_path.write_text(json.dumps(receipts, indent=2)+'\n')


if __name__ == '__main__':
    main()
