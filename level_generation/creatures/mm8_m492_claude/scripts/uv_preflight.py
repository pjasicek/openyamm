"""Project UV atlas raster, adapted from the verified Thug UV raster helper."""
import bpy,sys,os,numpy as np
from pathlib import Path
HERE=str(Path(__file__).resolve().parents[1]);N=2048
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'work/anim_uv.blend'))
for layer,slot in [('body',0),('head',1),('wings',2)]:
    b = bpy.data.objects['Body']; me = b.data
    co = np.array([tuple(v.co) for v in me.vertices])
    pv = np.zeros(len(co), np.int32); me.attributes['part'].data.foreach_get('value', pv)
    hd = np.array([f.material_index for f in me.polygons])
    names = [g.name for g in b.vertex_groups]
    dom = np.array([max(v.groups, key=lambda e: e.weight).group if len(v.groups) else -1 for v in me.vertices])
    uv = me.uv_layers.active.data
    piece = np.full((N, N), -1, np.int32); pos = np.zeros((N, N, 3), np.float32); bone = np.full((N, N), -1, np.int32)
    normal = np.zeros((N,N,3),np.float32); oral=np.zeros((N,N),bool); coverage=np.zeros((N,N),np.uint16)
    want_head = layer == 'head'
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        if hd[t.polygon_index] != slot:
            continue
        L = list(t.loops); V = list(t.vertices)
        P = np.array([tuple(uv[l].uv) for l in L]) * N
        x0, y0 = np.floor(P.min(0)).astype(int); x1, y1 = np.ceil(P.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, N - 1), min(y1, N - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, bb, c = P
        den = (bb[1] - c[1]) * (a[0] - c[0]) + (c[0] - bb[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((bb[1] - c[1]) * (xs - c[0]) + (c[0] - bb[0]) * (ys - c[1])) / den
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not m.any():
            continue
        iy = (N - 1 - (ys[m] - 0.5)).astype(int); ix = (xs[m] - 0.5).astype(int)    # image rows top-down
        piece[iy, ix] = pv[V[0]];oral[iy,ix]=bool(me.attributes['oral'].data[t.polygon_index].value)
        inside=(w0>=1e-5)&(w1>=1e-5)&(w2>=1e-5)
        oy=(N-1-(ys[inside]-.5)).astype(int);ox=(xs[inside]-.5).astype(int);coverage[oy,ox]+=1
        normal[iy, ix] = me.polygons[t.polygon_index].normal[:]
        pos[iy, ix] = (w0[m, None] * co[V[0]] + w1[m, None] * co[V[1]] + w2[m, None] * co[V[2]])
        bone[iy, ix] = dom[V[np.argmax([w0[m].mean(), w1[m].mean(), w2[m].mean()])]]
    np.savez_compressed(os.path.join(HERE, 'work', f'uvraster_{layer}.npz'), piece=piece, pos=pos, bone=bone, normal=normal,
                        bone_names=np.array(names),oral=oral,coverage=coverage)
    print('RASTER', layer, N, 'covered', round(float((piece >= 0).mean()), 3), 'pieces', sorted(set(np.unique(piece)) - {-1}))

import json
from mathutils import Vector
report={}
for label in ['body','head','wings']:
 d=np.load(os.path.join(HERE,'work',f'uvraster_{label}.npz'));coverage=d['coverage'];used=int((coverage>0).sum());overlap=int((coverage>1).sum())
 report[label]={'covered':used,'overlapping':overlap};assert used>10000 and overlap<max(32,used*.001),(label,report[label])
Path(HERE,'work/uv_coverage.json').write_text(json.dumps(report,indent=2)+'\n')
rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.data.objects['MouthFire'].hide_render=True;sc=bpy.context.scene
im=bpy.data.images.new('UV checker',1024,1024);im.generated_type='COLOR_GRID'
for mat in b.data.materials:
 nt=mat.node_tree;node=nt.nodes.new('ShaderNodeTexImage');node.image=im;nt.nodes.active=node;nt.links.new(node.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='TEXTURE';sc.display.shading.light='STUDIO';sc.render.resolution_x=1200;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('UV camera',bpy.data.cameras.new('UV camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,target,scale,direction in [('quarter',(0,-.02,.21),1.1,(1,-1,.5)),('rear',(0,-.02,.21),1.1,(-1,1,.5)),('head',(0,-.34,.31),.26,(1,-1,.1))]:
 target=Vector(target);cam.location=target+Vector(direction)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 sc.render.filepath=str(Path(HERE,'review',f'uv_{name}.png'));bpy.ops.render.render(write_still=True)
print('UV_PREFLIGHT',report)
