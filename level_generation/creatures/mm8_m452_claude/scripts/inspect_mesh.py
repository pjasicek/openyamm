import bpy, sys, json, math
from pathlib import Path
from mathutils import Vector, Matrix
P=Path(__file__).resolve().parents[1]
job=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'smart_topology_v1'
sys.path.insert(0,str(P/'scripts'))
from common_rat import render_ortho
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/f'meshy/{job}/model_urls_glb.glb'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
print('IMPORT',[(o.name,len(o.data.vertices),list(o.dimensions)) for o in meshes])
bpy.ops.object.select_all(action='DESELECT')
for o in meshes: o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.join()
mesh=bpy.context.object
mesh.parent=None
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
mesh.name=mesh.data.name='Rat'
if job=='smart_topology_v2':
    mesh.data.transform(Matrix.Rotation(math.pi/2,4,'Z'))
zmin=min(v.co.z for v in mesh.data.vertices)
for v in mesh.data.vertices: v.co.z-=zmin
for f in mesh.data.polygons: f.use_smooth=True
verts=[list(v.co) for v in mesh.data.vertices]
bounds=[[min(v[k] for v in verts),max(v[k] for v in verts)] for k in range(3)]
print('BOUNDS',bounds)
(P/f'work/{job}_mesh_info.json').write_text(json.dumps({'bounds':bounds,'vertices':verts,'faces':len(mesh.data.polygons)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{job}_body.blend'))
c=Vector([(lo+hi)/2 for lo,hi in bounds]); c.x=0
scale=max(hi-lo for lo,hi in bounds)*1.12
for name,axis in [('side',(4,0,0)),('top',(0,0,4)),('front',(0,-4,0)),('quarter',(3,-4,2))]:
    render_ortho(c+Vector(axis),c,scale,str(P/('review/'+job+'_'+name+'.png')),res=(1200,1200) if name=='top' else (1400,900))
