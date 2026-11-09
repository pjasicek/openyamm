"""Transfer the full-silhouette Meshy body UVs; preserve the selected head UVs, rig and actions."""
import bpy,sys,os,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
src_blend=str(P/'work/anim_uv.blend');job=str(P/'meshy/body_retexture_v1');out=str(P/'work/textured_master.blend');LAYER='UVMap'
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; LAYER=me.uv_layers.active.name
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.abspath(job), 'model_urls_glb.glb'))
src = max((o for o in bpy.data.objects if o not in before and o.type == 'MESH'), key=lambda o: len(o.data.polygons))
S = np.array([tuple(src.matrix_world @ v.co) for v in src.data.vertices])
T = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
# The head-only upload included a high fingertip island; retain its unused UV space, but texture fingers from the body.
for p in me.polygons:
    if p.material_index==1 and abs(sum(me.vertices[v].co.x for v in p.vertices)/len(p.vertices))>.32:p.material_index=0
hd = np.array([p.material_index for p in me.polygons])
polys = [p for p in me.polygons if hd[p.index] == 0]
# the body upload is the WHOLE mesh: fit on all of it (a box of the non-head faces is shorter when the scalp is in the
# head set - goblin: 196 mm mismatch); the head upload is the head faces alone
Tsub = T
scale = (Tsub.max(0) - Tsub.min(0)).max() / (S.max(0) - S.min(0)).max()
S = S * scale + ((Tsub.max(0) + Tsub.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale)
# A retexture may omit zero-area faces and recenter the bounding box; fit unchanged vertices robustly.
target_tree=kdtree.KDTree(len(T))
for i,p in enumerate(T):target_tree.insert(Vector(p),i)
target_tree.balance()
for _ in range(8):
    hits=[target_tree.find(Vector(p))for p in S];nearest=np.array([T[h[1]]for h in hits]);dist=np.array([h[2]for h in hits]);use=dist<=np.percentile(dist,90);ss=S[use];tt=nearest[use];sc0=ss.mean(0);tc0=tt.mean(0);factor=np.sum((ss-sc0)*(tt-tc0))/np.sum((ss-sc0)**2);S=(S-sc0)*factor+tc0
print('VERTEX_CORRESPONDENCE',np.percentile([target_tree.find(Vector(p))[2]for p in S],[0,50,90,99,100]),flush=True)
suv = src.data.uv_layers.active.data
tree = kdtree.KDTree(len(src.data.polygons))
for p in src.data.polygons:
    tree.insert(Vector(S[list(p.vertices)].mean(0)), p.index)
tree.balance()
if LAYER not in me.uv_layers:
    me.uv_layers.new(name=LAYER)
tuv = me.uv_layers[LAYER].data
# Meshy omitted twelve interior/cut faces. Recover their UV corners only where unchanged vertices share one UV chart.
parents=list(range(len(S)))
def root(i):
    while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
    return i
for f in src.data.polygons:
    for v in f.vertices:parents[root(v)]=root(f.vertices[0])
source_tree=kdtree.KDTree(len(S))
for i,p in enumerate(S):source_tree.insert(Vector(p),i)
source_tree.balance();vertex_uv={}
for f in src.data.polygons:
    for vi,li in zip(f.vertices,f.loop_indices):vertex_uv[vi]=suv[li].uv.copy()
missing=[]
worst, mism = 0.0, 0
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d)
    if d>.001:
        corner_error=max(source_tree.find(Vector(T[vi]))[2]for vi in p.vertices);assert corner_error<.025,(p.index,corner_error)
        missing.append({'face':p.index,'centroid_distance_m':d,'area_m2':p.area,'max_corner_distance_m':corner_error})
        continue
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
# Explicitly bake the twelve omitted interior/cut faces into a new 128-pixel strip; no UV seam guessing.
from mathutils.bvhtree import BVHTree
surface=BVHTree.FromPolygons([Vector(v)for v in S],[list(f.vertices)for f in src.data.polygons],all_triangles=True)
source_uv=[];output_pixels=[]
for p in polys:
    for li in p.loop_indices:tuv[li].uv.y*=2048/2176
for tile,item in enumerate(missing):
    p=me.polygons[item['face']];xyz=T[list(p.vertices)];corners=np.array([[tile*128+8,8],[tile*128+120,8],[tile*128+8,120]],float)
    for li,xy in zip(p.loop_indices,corners):tuv[li].uv=(xy[0]/2048,1-xy[1]/2176)
    for iy in range(128):
        for ix in range(128):
            w1=max(0,(ix-8)/112);w2=max(0,(iy-8)/112)
            if w1+w2>1:w1,w2=w1/(w1+w2),w2/(w1+w2)
            point=xyz[0]*(1-w1-w2)+xyz[1]*w1+xyz[2]*w2;loc,n,si,dist=surface.find_nearest(Vector(point));sp=src.data.polygons[si];tri=S[list(sp.vertices)];M=np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]);bary=np.linalg.lstsq(M,np.array(loc)-tri[0],rcond=None)[0];bary=np.clip(bary,0,1)
            if bary.sum()>1:bary/=bary.sum()
            uv=np.array([suv[l].uv[:]for l in sp.loop_indices]);pointuv=uv[0]*(1-bary.sum())+uv[1]*bary[0]+uv[2]*bary[1];source_uv.append(pointuv);output_pixels.append((iy,tile*128+ix))
np.savez_compressed(P/'work/body_missing_uv.npz',source_uv=source_uv,output_pixels=output_pixels)
(P/'work/body_uv_transfer.json').write_text(json.dumps({'max_centroid_error':worst,'corner_mismatches':mism,'body_faces':len(polys),'source_faces':len(src.data.polygons),'omitted_faces_with_verified_corners':missing},indent=2))
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
assert len(missing)==12 and mism == 0, f'UV mismatch {worst*1000:.3f} mm, {mism} faces'
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers[LAYER]
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
