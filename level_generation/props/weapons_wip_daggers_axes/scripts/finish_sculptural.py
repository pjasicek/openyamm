"""Add two static LODs to each reviewed sculptural weapon, keeping its baked UVs/materials."""
import json,sys,subprocess
from pathlib import Path
import bmesh,bpy
import numpy as np

P=Path(__file__).resolve().parents[1]; R=P.parents[2]
sys.path.insert(0,str(R/'level_generation/props/projectiles_claude/scripts'))
from projlib import fix_winding

designs=json.loads((P/'designs.json').read_text())
for name in sys.argv[sys.argv.index('--')+1:]:
    d=designs[name]; assert d['route']=='codex'
    source=P/'work/codex_tex'/f'{name}_export.glb';assert source.exists()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==1
    base=objects[0];base.name=name
    for material in base.data.materials:
        bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        node=bsdf.inputs['Base Color'].links[0].from_node;assert node.type=='TEX_IMAGE'
        img=node.image;pixels=np.array(img.pixels[:],dtype=np.float32).reshape(-1,4)
        pixels[:,:3]=np.clip(pixels[:,:3],30/255,243/255);img.pixels[:]=pixels.ravel()
        img.filepath_raw=str(P/'work/codex_tex/textures'/f'{name}_basecolor.png');img.file_format='PNG';img.save()
        node.image=bpy.data.images.load(img.filepath_raw,check_existing=False)
    # Restore shared topology across the GLB's normal/UV vertex splits before reducing either LOD.
    bm=bmesh.new();bm.from_mesh(base.data);bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(base.data);bm.free()
    bpy.context.view_layer.objects.active=base
    if base.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bpy.ops.object.shade_smooth_by_angle(angle=0.6981317008)
    fix_winding(base)
    counts=[sum(len(f.vertices)-2 for f in base.data.polygons)]
    for level,ratio in [(1,.5),(2,.25)]:
        ob=base.copy();ob.data=base.data.copy();ob.name=f'{name}_LOD{level}';bpy.context.collection.objects.link(ob)
        bpy.context.view_layer.objects.active=ob
        mod=ob.modifiers.new('silhouette LOD','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-7)
        bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(ob.data);bm.free()
        assert all(f.area>1e-10 for f in ob.data.polygons),(name,level,'degenerate LOD')
        lo=[min(v.co[a] for v in ob.data.vertices) for a in range(3)]
        hi=[max(v.co[a] for v in ob.data.vertices) for a in range(3)]
        for v in ob.data.vertices:
            v.co.x-=(lo[0]+hi[0])/2;v.co.y-=(lo[1]+hi[1])/2;v.co.z-=lo[2]
        ob.data.update();bpy.context.view_layer.update()
        fix_winding(ob)
        counts.append(len(ob.data.polygons))
    assert counts[0]>counts[1]>counts[2]
    bpy.ops.object.select_all(action='SELECT')
    raw=P/'work/codex_tex'/f'{name}_lods.glb'
    bpy.ops.export_scene.gltf(filepath=str(raw),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_skins=False,export_morph=False)
    for icon in d['icons']:
        destination=P/'work/exports'/f'w02_{icon}_export.glb'
        subprocess.run(['/usr/bin/python3',str(R/'tools/link_static_model_lods.py'),str(raw),str(destination)],check=True)
        subprocess.run(['/usr/bin/python3',str(P/'scripts/ground_lods.py'),str(destination)],check=True)
    (P/'work'/f'{name}_lods.json').write_text(json.dumps({'triangles':counts,'icons':d['icons']},indent=2)+'\n')
    print('FINISHED',name,counts,flush=True)
