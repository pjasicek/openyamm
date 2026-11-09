"""Prepare the four justified Smart Topology replacements; retain unmodified downloads and receipts."""
import json,sys
from pathlib import Path
import bmesh,bpy,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
from repair_geometry import activate,closed_normals,voxel_union,finish,cavity
from thicken_trial import thicken


def main():
    for icon in sys.argv[sys.argv.index('--')+1:]:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        source=P/f'meshy/geometryfinish_{icon}_st_v1/model_urls_glb.glb'
        bpy.ops.import_scene.gltf(filepath=str(source))
        objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
        for o in bpy.context.scene.objects:o.select_set(o in objects)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();obj=objects[0]
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        for other in list(bpy.context.scene.objects):
            if other!=obj:bpy.data.objects.remove(other,do_unlink=True)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
        # Split branched Smart Topology seams before closing the local surface patches.
        bmesh.ops.split_edges(bm,edges=[e for e in bm.edges if len(e.link_faces)>2])
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        has_open=any(e.is_boundary for e in bm.edges)
        bm.to_mesh(obj.data);bm.free()
        activate(obj)
        if has_open:obj=thicken(obj,.005)
        closed_normals(obj,fill=False)
        print('MESH_NORMALS',icon,obj.data.has_custom_normals,[a.name for a in obj.data.attributes],flush=True)
        if icon in ['item124','item125']:
            for v in obj.data.vertices:v.co.z*=.70
        elif icon=='6crown1':
            points=np.array([v.co[:] for v in obj.data.vertices]);_,axes=np.linalg.eigh(np.cov(points.T))
            axis=Vector(axes[:,0]);axis=axis if axis.z>0 else -axis
            rotation=axis.rotation_difference(Vector((0,0,1)))
            for v in obj.data.vertices:v.co=rotation@v.co
        elif icon=='6hat1':
            pass
        finish(obj,'equipment_'+icon,3400 if icon=='6crown1' else 3200)


if __name__=='__main__':main()
