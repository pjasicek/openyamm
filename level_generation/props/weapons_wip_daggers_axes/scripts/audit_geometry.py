"""Topology, UV seam and texel-density audit of this worker's authored meshes."""
import json,math,sys
from pathlib import Path
import bpy,bmesh
P=Path(__file__).resolve().parents[1];rows={}
only=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set()
for name,d in json.loads((P/'designs.json').read_text()).items():
    if only and name not in only:continue
    path=P/('blends' if d['route']=='blender' else 'work/codex_tex')/f'{name}.blend'
    if not path.exists():continue
    bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects[name]
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();uv=bm.loops.layers.uv.active;sharp=[]
    for e in bm.edges:
        if len(e.link_faces)!=2:continue
        if e.calc_face_angle()>math.radians(40) and (not e.smooth or not all(f.smooth for f in e.link_faces)):
            a,b=e.link_faces
            if all(not any(n.type=='TEX_IMAGE' for n in o.data.materials[f.material_index].node_tree.nodes) for f in [a,b]):continue
            lookup=lambda f:{l.vert.index:l[uv].uv.copy() for l in f.loops}
            au,bu=lookup(a),lookup(b)
            if all((au[v.index]-bu[v.index]).length<1e-5 for v in e.verts):sharp.append(e.index)
    area=sum(f.calc_area() for f in bm.faces);uvarea=0
    for f in bm.faces:
        coords=[l[uv].uv for l in f.loops]
        uvarea+=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(coords,coords[1:]+coords[:1])))/2
    rows[name]={'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),
        'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True),
        'area':area,'uv_area':uvarea,'texels_per_authoring_metre':1024*math.sqrt(uvarea/area),
        'hard_edges_without_uv_seam':len(sharp),'seam_edges':sharp}
    bm.free()
(P/'review/geometry_audit.json').write_text(json.dumps(rows,indent=2)+'\n')
print('AUDITED',len(rows),{n:{k:v[k] for k in ['boundary_edges','hard_edges_without_uv_seam']} for n,v in rows.items() if v['hard_edges_without_uv_seam'] or v['boundary_edges']})
assert all(v['hard_edges_without_uv_seam']==0 for v in rows.values()),'A hard edge has joined UVs'
