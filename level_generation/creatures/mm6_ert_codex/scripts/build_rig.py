"""Source-frame Earth Elemental rig, fitted joints and mesh-measured rigid stone fists."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ = lambda *p: os.path.join(HERE, *p)
ALL_SRC = json.load(open(W_('work', 'source_rest.json')))
SRC = {n:v for n,v in ALL_SRC.items() if 'Finger' not in n}
J = {k: Vector(v) for k, v in json.load(open(W_('work', 'joints_final.json')))['joints'].items()}
NAME = {'B_Pelvis': 'Pelvis', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck', 'B_Head': 'Head'}
for s in ('L', 'R'):
    for b in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot', 'Toe0'):
        NAME[f'B_{s}_{b}'] = f'{s}_{b}'
bpy.ops.wm.open_mainfile(filepath=W_('work', 'step1.blend'))
body = bpy.data.objects['Body']

# ---------------------------------------------------------------- heads and frames
order = []
def visit(n):
    order.append(n)
    for c in [k for k, v in SRC.items() if v['parent'] == n]:
        visit(c)
visit('B_Pelvis')
head, rot, swing = {}, {}, {}
for n in order:
    s = SRC[n]
    Rs = Matrix([Vector(r) for r in s['rot']])
    if n in NAME:
        head[n] = J[NAME[n]].copy()                             # fingers are placed after the hand's swing is known
    rot[n] = Rs
for n in order:
    s = SRC[n]
    c = s['child']
    if c and n in NAME and c in NAME:
        q = Vector(s['seg']).rotation_difference(head[c] - head[n])
    elif s['parent'] in swing:
        q = swing[s['parent']]
    else:
        q = Quaternion()
    if n == 'B_Pelvis':
        q = Quaternion()                                        # root keeps the source frame (Meshy's hips sit higher)
    swing[n] = q
    rot[n] = q.to_matrix() @ rot[n]
# Closed fists retain their geometry; frame direction is wrist -> fist centre, roll from the visible thumb side.
CO=np.array([v.co[:] for v in body.data.vertices]); hand_report={}
def basis(f,t):
 f=f/np.linalg.norm(f);t=t-f*(t@f);t=t/np.linalg.norm(t)
 return np.column_stack([f,t,np.cross(f,t)])
for sd,sg,thumb in [('L',1,(.32,-.42,1.54)),('R',-1,(-.55,-.49,1.18))]:
 n=f'B_{sd}_Hand';wr=np.array(head[n]);fa=np.array(head[f'B_{sd}_Forearm']);d=(wr-fa)/np.linalg.norm(wr-fa)
 mask=(CO[:,0]*sg>.23)&((CO-wr)@d>.055)&(np.linalg.norm(CO-wr,axis=1)<.42)
 hv=CO[mask];assert len(hv)>60,(sd,len(hv));c=hv.mean(0)
 f=c-wr;t=np.array(thumb)-c
 hsrc=np.array(ALL_SRC[n]['head']);fs=np.array(ALL_SRC[f'B_{sd}_Finger2']['head'])-hsrc
 ts=np.array(ALL_SRC[f'B_{sd}_Finger1']['head'])-np.array(ALL_SRC[f'B_{sd}_Finger4']['head'])
 q=Matrix((basis(f,t)@basis(fs,ts).T).tolist()).to_quaternion()
 swing[n]=q;rot[n]=q.to_matrix()@Matrix(SRC[n]['rot'])
 hand_report[sd]={'wrist':wr.tolist(),'fist_centre':c.tolist(),'thumb_landmark':list(thumb),'vertices':int(mask.sum())}
json.dump(hand_report,open(W_('work','hand_frames.json'),'w'),indent=2)

# ---------------------------------------------------------------- armature
ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for n in order:
    eb = ad.edit_bones.new(n)
    R = rot[n]
    c = SRC[n]['child']
    L = (head[c] - head[n]).length if c in head and (head[c] - head[n]).length > 1e-4 else 0.04
    eb.head = head[n]; eb.tail = head[n] + R.col[1] * L
    eb.align_roll(R.col[2])
for n in order:
    if SRC[n]['parent'] in SRC:                                # B_Pelvis's parent is the source's Motion root (dropped)
        ad.edit_bones[n].parent = ad.edit_bones[SRC[n]['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
# frame check: edit-bone matrices must equal the intended frames
err = max(math.degrees((rig.data.bones[n].matrix_local.to_3x3().to_quaternion()).rotation_difference(rot[n].to_quaternion()).angle)
          for n in order)
print('RIG bones', len(order), 'max frame error deg', round(err, 3))
assert err<.1,err

# ---------------------------------------------------------------- weights from Meshy's auto-rig
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=W_('meshy', 'rig_v1', 'result_rigged_character_glb_url.glb'))
new = set(bpy.data.objects) - before
src_mesh = max((o for o in new if o.type == 'MESH'), key=lambda o: len(o.data.vertices))   # set order is random; skip helpers
src_arm = next(o for o in new if o.type == 'ARMATURE')
M2B = {'Hips': 'B_Pelvis', 'Spine02': 'B_Spine', 'Spine01': 'B_Spine1', 'Spine': 'B_Spine2', 'neck': 'B_Neck', 'Head': 'B_Head',
       'head_end': 'B_Head', 'headfront': 'B_Head'}
for side, s in (('Left', 'L'), ('Right', 'R')):
    M2B.update({f'{side}Shoulder': f'B_{s}_Clavicle', f'{side}Arm': f'B_{s}_UpperArm', f'{side}ForeArm': f'B_{s}_Forearm',
                f'{side}Hand': f'B_{s}_Hand', f'{side}UpLeg': f'B_{s}_Thigh', f'{side}Leg': f'B_{s}_Calf',
                f'{side}Foot': f'B_{s}_Foot', f'{side}ToeBase': f'B_{s}_Toe0'})
deps = bpy.context.evaluated_depsgraph_get()
src_co = np.array([tuple(src_mesh.matrix_world @ v.co) for v in src_mesh.data.vertices])
dst_co = np.array([tuple(body.matrix_world @ v.co) for v in body.data.vertices])
if 'orig_co' in body.data.attributes:                          # match against the unmodified positions (step1 edits)
    oc = np.zeros(len(dst_co) * 3); body.data.attributes['orig_co'].data.foreach_get('vector', oc); dst_co = oc.reshape(-1, 3)
# Meshy returns the mesh in its own placement: match bounding boxes (as meshy_joints.py does)
sc = (dst_co[:, 2].max() - dst_co[:, 2].min()) / (src_co[:, 2].max() - src_co[:, 2].min())
cen = lambda c: np.array([(c[:, 0].max() + c[:, 0].min()) / 2, (c[:, 1].max() + c[:, 1].min()) / 2, c[:, 2].min()])
src_co = src_co * sc + (cen(dst_co) - cen(src_co) * sc)
from mathutils.kdtree import KDTree                             # Blender's Python has no scipy
kd = KDTree(len(src_co))
for i, c in enumerate(src_co):
    kd.insert(c, i)
kd.balance()
hits = [kd.find(c) for c in dst_co]
idx = [h[1] for h in hits]; d = np.array([h[2] for h in hits])
assert d.max()<.003,('Rig return changed geometry',float(d.max()))
print('WEIGHTS nearest-vertex transfer: max distance mm', round(float(d.max()) * 1000, 2), 'mean', round(float(d.mean()) * 1000, 3))
gidx = {g.index: M2B.get(g.name, g.name) for g in src_mesh.vertex_groups}   # renaming would add .001 suffixes
body.vertex_groups.clear()
groups = {n: body.vertex_groups.new(name=n) for n in order}
unmapped = set()
for vi, si in enumerate(idx):
    for ge in src_mesh.data.vertices[si].groups:
        n = gidx[ge.group]
        if n in groups and ge.weight > 1e-4:
            groups[n].add([vi], ge.weight, 'ADD')
        elif ge.weight > 1e-4:
            unmapped.add(n)
print('WEIGHTS unmapped Meshy groups', sorted(unmapped))
# Move the service's premature hand bend to the measured wrist, and make each curled stone fist rigid.
for sd,sg in [('L',1),('R',-1)]:
 hn=f'B_{sd}_Hand';fn=f'B_{sd}_Forearm';wr=np.array(head[hn]);d=(wr-np.array(head[fn]));d/=np.linalg.norm(d)
 hi,fi=groups[hn].index,groups[fn].index
 for v in body.data.vertices:
  c=np.array(v.co);weights={e.group:e.weight for e in v.groups}
  total=weights.get(hi,0)+weights.get(fi,0)
  if c[0]*sg>.23 and np.linalg.norm(c-wr)<.52 and total>.1:
   t=float(np.clip(((c-wr)@d+.075)/.11,0,1));t=t*t*(3-2*t)
   groups[hn].add([v.index],total*t,'REPLACE');groups[fn].add([v.index],total*(1-t),'REPLACE')
   if (c-wr)@d>.04:
    for group in body.vertex_groups:group.remove([v.index])
    groups[hn].add([v.index],1,'REPLACE')
# The brow and jaw belong to the skull; short-neck stone anatomy must not be dragged by the shoulders.
for v in body.data.vertices:
 if v.co.z>2.01:
  for group in body.vertex_groups:group.remove([v.index])
  groups['B_Head'].add([v.index],1,'REPLACE')
for v in body.data.vertices:
 total=sum(e.weight for e in v.groups);assert total>.99,('Unweighted vertex',v.index,total)
 assert sum(e.weight>.0001 for e in v.groups)<=8
 for e in list(v.groups):
  body.vertex_groups[e.group].add([v.index],e.weight/total,'REPLACE')
for o in new:
    bpy.data.objects.remove(o, do_unlink=True)
body.parent = rig
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
bpy.context.scene['rig_offsets'] = json.dumps({n: {'q': list(swing[n]), 'R_src': [list(r) for r in SRC[n]['rot']]} for n in order})
bpy.ops.wm.save_as_mainfile(filepath=W_('work', 'rig_v1.blend'))
