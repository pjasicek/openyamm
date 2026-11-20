"""Fit a closed, textured hair volume beneath the source's disconnected strands."""
from pathlib import Path
import math, json, runpy
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

p = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/rig_textured_uv.blend'))
body = bpy.data.objects['Body']; mesh = body.data
reference = np.load(p / 'work/hair_reference.npz')['base']
height, width = reference.shape[:2]
hair_faces, hair_uvs = [], []
for face in mesh.polygons:
    if not all(mesh.attributes['piece'].data[i].value == 104 for i in face.vertices):
        continue
    uv = np.array([mesh.uv_layers['HeadUV'].data[i].uv[:] for i in face.loop_indices])
    coords = np.array([mesh.vertices[i].co[:] for i in face.vertices])
    center = coords.mean(0); sample = uv.mean(0)
    color = reference[min(height-1, int((1-sample[1])*height)), min(width-1, int(sample[0]*width))]
    # Exclude the face, stubble and ears; dark hair continues down the sides and nape.
    if center[2] > 1.545 and color.mean() < .42 and (center[2] > 1.64 or center[1] > .005):
        hair_faces.append(tuple(face.vertices)); hair_uvs.append(uv)
assert len(hair_faces) > 500, len(hair_faces)
points = [v.co.copy() for v in mesh.vertices]
tree = BVHTree.FromPolygons(points, hair_faces, all_triangles=True)
origin = Vector((-.024, .031, 1.602))
cols, rows = 48, 12
directions, radii = [], []
for row in range(rows + 1):
    for col in range(cols):
        angle = 2*math.pi*col/cols
        end = 1.90 + .70*math.sin(angle)
        theta = end*row/rows
        direction = Vector((math.sin(theta)*math.cos(angle), math.sin(theta)*math.sin(angle), math.cos(theta)))
        directions.append(direction)
        hits = []; start = origin.copy()
        for _ in range(24):
            location, normal, index, distance = tree.ray_cast(start, direction, .25)
            if location is None: break
            hits.append((location-origin).length)
            start = location + direction*.00005
        fallback = 1/math.sqrt((direction.x/.081)**2 + (direction.y/.088)**2 + (direction.z/.090)**2)
        radii.append(max(hits) if hits else fallback)
radii = np.array(radii).reshape(rows+1, cols)
for _ in range(2):
    radii = .5*radii + .125*(np.roll(radii, 1, 1)+np.roll(radii, -1, 1)+np.vstack((radii[:1], radii[:-1]))+np.vstack((radii[1:], radii[-1:])))
radii -= .002
radii[0] = min(float(np.median(radii[0])), .092)
# The front hairline stays above the forehead; the hidden lower rim lies inside the head.
vertices = [tuple(origin + directions[0]*float(radii[0,0]))]
for row in range(1, rows+1):
    for col in range(cols):
        co = origin + directions[row*cols+col]*float(radii[row,col])
        vertices.append(tuple(co))
# A second rim sinks into the skin so the hair has no open band at the ears or nape.
for col in range(cols):
    angle=2*math.pi*col/cols
    back=min(1,max(0,(math.sin(angle)+.5)/.5)); back=back*back*(3-2*back)
    side=(1-abs(math.sin(angle)))*back
    co=Vector((-.020+.060*math.sin(2.30)*math.cos(angle)*(1-.1*side),
               .025+.057*math.sin(2.30)*math.sin(angle)+.015*side,
               1.604+.072*math.cos(2.30)))
    co.z-=max(0,co.z-(1.54-.04*max(0,math.sin(angle))))*back
    vertices.append(tuple(co))
rows += 1
vertices.append(tuple(origin + Vector((0, 0, -.110))))
faces = []
for col in range(cols):
    faces.append((0, 1+col, 1+(col+1)%cols))
for row in range(rows-1):
    for col in range(cols):
        a = 1+row*cols+col; b = 1+row*cols+(col+1)%cols
        c = b+cols; d = a+cols
        faces.extend(((a,d,c),(a,c,b)))
bottom = len(vertices)-1
for col in range(cols):
    faces.append((bottom, 1+(rows-1)*cols+(col+1)%cols, 1+(rows-1)*cols+col))

atlas = np.load(p / 'work/uvraster_HeadUV.npz')
occupied = atlas['coverage'] & (atlas['piece'] != 4)
N = 2048; size = 192
integral = np.pad(occupied.astype(np.int32), ((1,0),(1,0))).cumsum(0).cumsum(1)
areas = integral[size:,size:]-integral[:-size,size:]-integral[size:,:-size]+integral[:-size,:-size]
free = np.argwhere(areas[::4,::4] == 0)
assert len(free), 'No free hair texture chart'
y,x = free[0]*4
center_uv = Vector(((x+size/2)/N, 1-(y+size/2)/N)); radius = (size/2-12)/N
uvs = [center_uv]
for row in range(1,rows+1):
    for col in range(cols):
        angle = 2*math.pi*col/cols
        uvs.append(center_uv + Vector((math.cos(angle),math.sin(angle)))*radius*row/rows)
uvs.append(Vector((.003,.003)))

bm = bmesh.new(); bm.from_mesh(mesh); piece = bm.verts.layers.int['piece']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[piece] == 105], context='VERTS')
bm.to_mesh(mesh); bm.free()
cap_mesh = bpy.data.meshes.new('ContinuousHair'); cap_mesh.from_pydata(vertices, [], faces); cap_mesh.update()
cap = bpy.data.objects.new('ContinuousHair', cap_mesh); bpy.context.collection.objects.link(cap)
bm = bmesh.new(); bm.from_mesh(cap_mesh); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
assert all(e.is_manifold for e in bm.edges)
if bm.calc_volume(signed=True) < 0: bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
volume = bm.calc_volume(signed=True); assert volume > .0005
bm.to_mesh(cap_mesh); bm.free()
for name in ('HeadUV','UVMap'):
    layer = cap_mesh.uv_layers.new(name=name)
    for face in cap_mesh.polygons:
        for li in face.loop_indices:
            vi = cap_mesh.loops[li].vertex_index
            # The hidden underside uses a separate small disk in the retired scalp chart.
            if bottom in face.vertices:
                if vi == bottom: layer.data[li].uv = (.010,.010)
                else:
                    angle = 2*math.pi*((vi-1)%cols)/cols
                    layer.data[li].uv = (.010+.003*math.cos(angle), .010+.003*math.sin(angle))
            else: layer.data[li].uv = uvs[vi]
for name,domain,value in [('head','FACE',1),('piece','POINT',105),('region','POINT',4)]:
    attribute = cap_mesh.attributes.new(name,'INT',domain)
    attribute.data.foreach_set('value',[value]*len(attribute.data))
cap.vertex_groups.new(name='B_Head').add(list(range(len(vertices))),1,'REPLACE')
for face in cap_mesh.polygons: face.use_smooth = True
for ob in bpy.data.objects: ob.select_set(ob in (body,cap))
bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=str(p / 'work/rig_textured_uv.blend'))
runpy.run_path(str(p / 'scripts/raster_head_v2.py'),run_name='__main__')
atlas = np.load(p / 'work/uvraster_HeadUV.npz'); mask = atlas['coverage'] & (atlas['piece'] == 4)
positions = atlas['pos'][mask]; colors = []
for position in positions:
    location, normal, index, distance = tree.find_nearest(Vector(position))
    assert location is not None
    a,b,c = (points[i] for i in hair_faces[index])
    weights = barycentric_transform(location,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
    uv = np.array(weights) @ hair_uvs[index]
    sx = np.clip(uv[0]*width-.5,0,width-1); sy = np.clip((1-uv[1])*height-.5,0,height-1)
    ix,iy = int(sx),int(sy); fx,fy = sx-ix,sy-iy
    jx,jy = min(ix+1,width-1),min(iy+1,height-1)
    colors.append((1-fy)*((1-fx)*reference[iy,ix]+fx*reference[iy,jx])+fy*((1-fx)*reference[jy,ix]+fx*reference[jy,jx]))
np.savez_compressed(p / 'work/hair_volume_paint.npz',mask=mask,base=np.array(colors,dtype=np.float32))
report = {'source_hair_triangles':len(hair_faces),'core_triangles':len(faces),'boundary_edges':0,
          'volume_m3':volume,'texture_chart_pixels':int(mask.sum()),'rigid_bone':'B_Head'}
(p / 'work/hair_volume.json').write_text(json.dumps(report,indent=2)+'\n'); print('HAIR_VOLUME',report)
