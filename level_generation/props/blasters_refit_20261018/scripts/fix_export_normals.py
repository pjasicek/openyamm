"""Repair only opposed corner normals on the final textured exports; preserve geometry and artwork."""
from pathlib import Path
import sys

import bpy
from mathutils import Vector

P=Path(__file__).resolve().parents[1]


def main():
    names=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set()
    for path in sorted((P/'work/meshy').glob('*_export.glb')):
        if names and path.stem.removesuffix('_export') not in names:continue
        bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
        objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
        fixed=0
        for o in objects:
            normals=[n.vector.copy() for n in o.data.corner_normals]
            for face in o.data.polygons:
                mean=sum((normals[i] for i in face.loop_indices),Vector())/len(face.loop_indices)
                if mean.dot(face.normal)<.01:
                    fixed+=1
                    for i in face.loop_indices:normals[i]=face.normal.copy()
            o.data.normals_split_custom_set(normals)
        if fixed:
            temporary=path.with_name(path.stem+'_normals.glb')
            bpy.ops.export_scene.gltf(filepath=str(temporary),export_format='GLB',use_selection=True,export_yup=True)
            temporary.replace(path)
        print('NORMALS',path.name,fixed,flush=True)


if __name__=='__main__':main()
