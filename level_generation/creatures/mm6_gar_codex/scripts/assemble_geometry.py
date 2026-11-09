"""Fit the repaired detailed head to the retained body, preserving all wing membranes."""
import bpy,bmesh,json,sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_digits.blend'))
body=bpy.data.objects['Gargoyle']; body.name='Body'
bm=bmesh.new(); bm.from_mesh(body.data)
old_head=[v for v in bm.verts if (v.co.z>1.66 or (v.co.z>1.58 and v.co.y<-.10) or (v.co.z>1.40 and v.co.y<-.13 and abs(v.co.x)<.065)) and abs(v.co.x)<.225 and v.co.y<.105]
assert len(old_head)>200 and len(old_head)<2500,len(old_head)
bmesh.ops.delete(bm,geom=old_head,context='VERTS')
loose=[v for v in bm.verts if not v.link_faces]
if loose: bmesh.ops.delete(bm,geom=loose,context='VERTS')
# Remove the old floating teeth/tongue and close only the opening left by head removal.
seen=set(); fragments=[]
for seed in bm.verts:
    if seed in seen: continue
    seen.add(seed); stack=[seed]; comp=[]
    while stack:
        v=stack.pop(); comp.append(v)
        for e in v.link_edges:
            other=e.other_vert(v)
            if other not in seen: seen.add(other); stack.append(other)
    if len(comp)<150 and min(v.co.z for v in comp)>1.3: fragments.extend(comp)
if fragments:bmesh.ops.delete(bm,geom=fragments,context='VERTS')
neck_edges=[e for e in bm.edges if e.is_boundary and all(v.co.z>1.39 and abs(v.co.x)<.23 and v.co.y<.12 for v in e.verts)]
if neck_edges:bmesh.ops.holes_fill(bm,edges=neck_edges,sides=0)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(body.data); bm.free()
with bpy.data.libraries.load(str(P/'work/head_geometry_clean.blend'),link=False) as (src,dst):
    dst.objects=['GargoyleHead']
head=dst.objects[0]; bpy.context.scene.collection.objects.link(head)
for v in head.data.vertices:
    original=v.co.copy(); v.co=original*.38+Vector((0,-.03,1.50))
    # Bend the lower neck backward into the original torso, retaining the projecting jaw.
    if original.z<.30 and original.y>-.05:
        u=max(0,min(1,(.30-original.z)/.23)); w=u*u*(3-2*u)
        w*=max(0,min(1,(original.y+.05)/.10))
        inside=Vector((v.co.x*.40,.09+(original.y-.2)*.05,v.co.z))
        v.co=v.co.lerp(inside,w)
if body.data.has_custom_normals:body.data.normals_split_custom_set([(0,0,0)]*len(body.data.loops))
head.name='Head'; body.color=head.color=(.52,.55,.57,1)
for obj in [body,head]:
    for p in obj.data.polygons: p.use_smooth=True
body.data.materials.clear(); head.data.materials.clear()
for name,obj in [('GargoyleBody',body),('GargoyleHead',head)]:
    mat=bpy.data.materials.new(name); mat.diffuse_color=(.52,.55,.57,1); obj.data.materials.append(mat)
scene=bpy.context.scene; scene.world=bpy.data.worlds.new('AssemblyReview'); common.workbench_clay(scene); scene.display.shading.color_type='OBJECT'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_assembled.blend'))
common.render_views(str(P/'review/assembled'),1.5,3.3,views=('front','left','back','three_quarter'),resolution=(800,1100))
common.render_views(str(P/'review/assembled_neck'),1.54,.68,views=('front','left','back','three_quarter'),resolution=(850,850),target=(0,-.1))
print('ASSEMBLED',len(body.data.vertices),len(head.data.vertices),'old head vertices removed',len(old_head))
