"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto our rigged body, after
mm6_wdm_claude/scripts/transfer_uv.py: the returned mesh has the same faces in its own placement; it is fitted back by
bounding box, each of our faces is matched to the returned face with the nearest centroid, and each corner takes the
UV of the nearest returned corner of that face. Writes layer 'UVMap' (the head faces keep their own 'HeadUV').
Reports the worst centroid mismatch and face-count agreement. Args: -- <in blend> <meshy job dir> <out blend>"""
import bpy, sys, os, json
from pathlib import Path
import numpy as np
import itertools
from mathutils import Vector, kdtree
a_ = sys.argv[sys.argv.index('--') + 1:]
src_blend, job, out = a_[:3]
LAYER = a_[3] if len(a_) > 3 else 'UVMap'          # 'HeadUV': only the head faces, fitted to their own bbox
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.abspath(job), 'model_urls_glb.glb'))
src = max((o for o in bpy.data.objects if o not in before and o.type == 'MESH'), key=lambda o: len(o.data.polygons))
S = np.array([tuple(src.matrix_world @ v.co) for v in src.data.vertices])
T = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
polys = [p for p in me.polygons if (hd[p.index] == 1) == (LAYER == 'HeadUV')]
# the body upload is the WHOLE mesh: fit on all of it (a box of the non-head faces is shorter when the scalp is in the
# head set - goblin: 196 mm mismatch); the head upload is the head faces alone
Tsub = T if LAYER == 'UVMap' else T[sorted({v for p in polys for v in p.vertices})]
scale = (Tsub.max(0) - Tsub.min(0)).max() / (S.max(0) - S.min(0)).max()
S = S * scale + ((Tsub.max(0) + Tsub.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale)
suv = src.data.uv_layers.active.data
tree = kdtree.KDTree(len(src.data.polygons))
for p in src.data.polygons:
    tree.insert(Vector(S[list(p.vertices)].mean(0)), p.index)
tree.balance()
if LAYER not in me.uv_layers:
    me.uv_layers.new(name=LAYER)
tuv = me.uv_layers[LAYER].data
# Missing return faces retain the original geometry and get a small atlas patch projected from the return.
reconstructed=[];missing_faces=[]
def reconstruct(face):missing_faces.append(face)
worst, mism = 0.0, 0
matched=set();corner_worst=0.0
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    candidates=[];tv=T[list(p.vertices)]
    for _,candidate,distance in tree.find_n(c,16):
        if candidate in matched:continue
        cp=src.data.polygons[candidate]
        if len(cp.vertices)!=len(p.vertices):continue
        for perm in itertools.permutations(range(len(cp.vertices))):
            err=float(np.linalg.norm(tv-S[list(cp.vertices)][list(perm)],axis=1).max())
            candidates.append((err,distance,candidate,perm))
    if not candidates or min(candidates)[0]>.0002:
        reconstruct(p);continue
    error,d,si,permutation=min(candidates);corner_worst=max(corner_worst,error);worst=max(worst,d);matched.add(si)
    sp=src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    corners=set()
    for li, vi, k in zip(p.loop_indices, p.vertices, permutation):
        assert k not in corners,(p.index,k,"duplicate corner")
        corners.add(k);corner_worst=max(corner_worst,float(np.linalg.norm(T[vi]-sco[k])))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
if missing_faces:
    from mathutils.bvhtree import BVHTree
    from mathutils.geometry import barycentric_transform
    N=2048;coverage=np.zeros((N,N),bool);missing_ids={p.index for p in missing_faces}
    def raster(q):
        a,b,c=np.array(q)*N;den=np.cross(b-a,c-a)
        if abs(den)<1e-12:return np.array([],int),np.array([],int),np.empty((0,3))
        lo=np.maximum(np.floor(np.minimum(np.minimum(a,b),c)).astype(int),0);hi=np.minimum(np.ceil(np.maximum(np.maximum(a,b),c)).astype(int),N-1)
        x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);w1=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/den;w2=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/den;m=(w1>=0)&(w2>=0)&(w1+w2<=1)
        return (x[m]-.5).astype(int),(y[m]-.5).astype(int),np.stack([1-w1[m]-w2[m],w1[m],w2[m]],-1)
    for p in polys:
        if p.index in missing_ids:continue
        x,y,w=raster([tuv[i].uv[:] for i in p.loop_indices]);coverage[y,x]=True
    bvh=BVHTree.FromPolygons(S.tolist(),[tuple(p.vertices) for p in src.data.polygons]);pixels=[];lookup=[];tiles=[]
    for p in missing_faces:
        tile=next(((x,y) for y in range(0,N-64,16) for x in range(0,N-64,16) if not coverage[y:y+64,x:x+64].any()),None);assert tile is not None
        xx,yy=tile;q=[((xx+8)/N,(yy+8)/N),((xx+56)/N,(yy+8)/N),((xx+8)/N,(yy+56)/N)]
        for li,uv in zip(p.loop_indices,q):tuv[li].uv=uv
        x,y,w=raster(q);positions=w@T[list(p.vertices)];maxdist=0
        for ix,iy,point in zip(x,y,positions):
            loc,norm,fi,dist=bvh.find_nearest(Vector(point));maxdist=max(maxdist,dist);sp=src.data.polygons[fi];uvs=[Vector((*suv[li].uv,0)) for li in sp.loop_indices];uv=barycentric_transform(loc,*[Vector(S[i]) for i in sp.vertices],*uvs);pixels.append([int(ix),int(N-1-iy)]);lookup.append(uv[:2])
        assert maxdist<.03,(p.index,maxdist)
        coverage[yy:yy+64,xx:xx+64]=True;tiles.append([xx,N-yy-64,64]);reconstructed.append({'face':p.index,'atlas_tile':tiles[-1],'max_projection_distance_m':maxdist,'normal':'flat on the small reconstructed fur patch'})
    np.savez_compressed(Path(__file__).resolve().parents[1]/'work/body_missing_face_lookup.npz',pixels=np.array(pixels),uv=np.array(lookup),tiles=np.array(tiles),size=N)
    print('RECONSTRUCTED UV',reconstructed)
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
assert mism==0 and worst<.0002 and corner_worst<.0002,(mism,worst,corner_worst)
(Path(__file__).resolve().parents[1]/'review'/f'uv_transfer_{LAYER}.json').write_text(json.dumps({'layer':LAYER,'target_faces':len(polys),'matched_faces':len(matched),'reconstructed_missing_faces':reconstructed,'returned_faces':len(src.data.polygons),'max_centroid_mismatch_m':worst,'corner_count_mismatches':mism,'max_corner_error_m':corner_worst,'unique_face_matches':len(matched),'pass':True},indent=2))
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
