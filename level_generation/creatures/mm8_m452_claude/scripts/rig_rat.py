"""Rat: import the Meshy Smart Topology mesh, ground it, build a quadruped deform skeleton from joints traced on
the mesh (leg/body slices), skin it with Blender automatic (heat) weights. Saves work/rig_v1.blend.
Forward is -Y, up +Z, character left +X."""
import bpy, os, sys, json
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'work/fit_body.blend'))
mesh=bpy.data.objects['Rat']
CHAINS={
 'Spine':(None,[(0,.07,.175),(0,.0,.178),(0,-.12,.20),(0,-.25,.20)]),
 'Neck':('Spine3',[(0,-.25,.20),(0,-.335,.20)]),
 'Head':('Neck1',[(0,-.335,.20),(0,-.49,.195)]),
 'Jaw':('Head',[(0,-.37,.182),(0,-.48,.17)]),
 'Tail':('Spine1',[(.002,.15,.20),(.011,.21,.191),(.025,.28,.18),(.041,.34,.135),(.068,.40,.059),(.094,.45,.032),(.114,.5,.012)]),
 'Front_L':('Spine3',[(.055,-.21,.165),(.055,-.17,.10),(.046,-.191,.033),(.049,-.25,.009)]),
 'Front_R':('Spine3',[(-.066,-.21,.165),(-.068,-.16,.10),(-.092,-.178,.033),(-.107,-.24,.009)]),
 'Hind_L':('Spine1',[(.047,.065,.18),(.065,.035,.12),(.093,.137,.033),(.102,.065,.009)]),
 'Hind_R':('Spine1',[(-.046,.065,.18),(-.062,.04,.12),(-.084,.146,.034),(-.096,.065,.009)]),
}
NAMES={'Spine':['Spine1','Spine2','Spine3'],'Neck':['Neck1'],'Head':['Head'],'Jaw':['Jaw'],
       'Tail':[f'Tail{i}' for i in range(1,7)]}
for side in 'LR':
 NAMES['Front_'+side]=[f'UpperArm_{side}',f'ForeArm_{side}',f'FrontPaw_{side}']
 NAMES['Hind_'+side]=[f'Thigh_{side}',f'Shin_{side}',f'HindPaw_{side}']

arm_data = bpy.data.armatures.new('Rat_Rig')
rig = bpy.data.objects.new('Rat_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
order = ['Spine', 'Neck', 'Head', 'Jaw', 'Tail', 'Front_L', 'Front_R', 'Hind_L', 'Hind_R']
for key in order:
    parent, pts = CHAINS[key]
    prev = eb[parent] if parent else None
    for i, name in enumerate(NAMES[key]):
        b = eb.new(name)
        b.head = pts[i]; b.tail = pts[i + 1]
        b.align_roll(Vector((0, 0, 1)) if key in ('Spine', 'Neck', 'Head', 'Jaw', 'Tail') else Vector((0, -1, 0)))
        b.parent = prev
        b.use_connect = prev is not None and i > 0
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
arm_data.bones['Jaw'].use_deform=False
# Bind the connected body alone; tiny detached eyes, teeth and whiskers destabilise bone heat.
import bmesh
bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table();unseen=set(bm.verts);pieces=[]
while unseen:
 seed=unseen.pop();piece={seed};stack=[seed]
 while stack:
  for edge in stack.pop().link_edges:
   for v in edge.verts:
    if v in unseen:unseen.remove(v);piece.add(v);stack.append(v)
 pieces.append(piece)
main=max(pieces,key=len);ids=sorted(v.index for v in main);remap={v:i for i,v in enumerate(ids)}
verts=[mesh.data.vertices[v].co.copy() for v in ids]
faces=[tuple(remap[v] for v in f.vertices) for f in mesh.data.polygons if all(v in remap for v in f.vertices)]
bm.free();me=bpy.data.meshes.new('HeatBody');me.from_pydata(verts,[],faces);me.update()
heat=bpy.data.objects.new('HeatBody',me);bpy.context.scene.collection.objects.link(heat)
for o in bpy.data.objects:o.select_set(o in (heat,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
missing=[v.index for v in me.vertices if not v.groups]
assert not missing, f'Connected-body heat weights failed: {len(missing)} vertices'
for g in heat.vertex_groups:mesh.vertex_groups.new(name=g.name)
for i,original in enumerate(ids):
 for g in me.vertices[i].groups:mesh.vertex_groups[g.group].add([original],g.weight,'REPLACE')
bpy.data.objects.remove(heat,do_unlink=True)
mesh.parent=rig;modifier=mesh.modifiers.new('RatSkin','ARMATURE');modifier.object=rig
arm_data.bones['Jaw'].use_deform=True
jaw=mesh.vertex_groups.get('Jaw') or mesh.vertex_groups.new(name='Jaw')
parts=mesh.data.attributes['anatomy'].data
# Explicit mouth ownership keeps opening the jaw from stretching the upper muzzle and incisors.
for v in mesh.data.vertices:
    x,y,z=v.co;part=parts[v.index].value
    if y<-.31 or part in (1,2,3,4):
        j=1.0 if part==3 else (0.0 if part in (1,2,4) else max(0,min(1,(-y-.385)/.025))*max(0,min(1,(.177-z)/.002)))
        h=max(0,min(1,(-y-.31)/.025))
        for g in mesh.vertex_groups:g.remove([v.index])
        for name,w in [('Jaw',j),('Head',(1-j)*h),('Neck1',(1-j)*(1-h))]:
            if w>1e-6:mesh.vertex_groups[name].add([v.index],w,'REPLACE')
# Detached paw/claw pieces inherit the nearest connected body weights, as in the quadruped playbook.
import bmesh
from mathutils.kdtree import KDTree
bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table();unseen=set(bm.verts);pieces=[]
while unseen:
    seed=unseen.pop();piece={seed};stack=[seed]
    while stack:
        for edge in stack.pop().link_edges:
            for v in edge.verts:
                if v in unseen:unseen.remove(v);piece.add(v);stack.append(v)
    pieces.append(piece)
pieces.sort(key=len,reverse=True);tree=KDTree(len(pieces[0]))
for v in pieces[0]:tree.insert(v.co,v.index)
tree.balance()
for piece in pieces[1:]:
    for v in piece:
        if v.co.y<-.30:continue
        _,idx,_=tree.find(v.co);weights=[(g.group,g.weight) for g in mesh.data.vertices[idx].groups]
        for g in mesh.vertex_groups:g.remove([v.index])
        for idx,w in weights:mesh.vertex_groups[idx].add([v.index],w,'REPLACE')
bm.free()
for o in bpy.data.objects:o.select_set(o==mesh)
bpy.context.view_layer.objects.active=mesh
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
empty = [v.index for v in mesh.data.vertices if not v.groups]
assert not empty, f'Unweighted vertices: {empty[:20]}'
print('RIGGED bones', len(arm_data.bones), 'unweighted verts', len(empty))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))

with open(os.path.join(HERE,'work/joints.json'),'w') as handle:json.dump(CHAINS,handle,indent=2)
