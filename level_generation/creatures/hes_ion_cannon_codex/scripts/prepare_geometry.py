"""Prepare a reduced, zone-split static cannon and a single-atlas neutral Meshy upload.
Uses the worked turret's component split / sharp-edge / Smart UV route, with source-specific face cuts.
Run in isolated Blender: -- study | uv <ratio>. Downloaded Meshy sources are never modified.
"""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parents[1]
SOURCE_SHA = "98b798a4f2d4daf4f71a049558a1ee3bc7ad43687e49d7f7bc1d783105977abd"
ZONES = ["Opaque", "GC_breech", "GC_pods", "GC_ring1", "GC_ring2", "GC_ring3", "GC_ring4", "GC_muzzle"]
SHARP = math.radians(38)


def select(objects):
    for o in bpy.context.scene.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]


def tris(objects):
    return sum(len(f.vertices)-2 for o in objects for f in o.data.polygons)


def shade(obj):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    if obj.get("zone",0)==0:
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = len(e.link_faces)==2 and e.calc_face_angle(0)<=SHARP
        if not e.smooth:
            e.seam = True
    bm.to_mesh(obj.data); bm.free()


def render(objects, prefix, views=("quarter",), zones=False, checker=False):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1200; scene.render.resolution_y = 800; scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.world = bpy.data.worlds.new("ReviewWorld"); scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .5
    for name, energy, angles in [("Key",2.5,(25,0,-35)),("Fill",1.2,(65,0,150))]:
        light = bpy.data.objects.new(name,bpy.data.lights.new(name,"SUN"));scene.collection.objects.link(light)
        light.data.energy = energy;light.rotation_euler = [math.radians(v) for v in angles]
    colours = [(.48,.5,.54,1),(.8,.08,.65,1),(.1,.7,.9,1),(.9,.2,.1,1),
               (.95,.6,.05,1),(.3,.75,.08,1),(.1,.25,.9,1),(.9,.8,.8,1)]
    image = None
    if checker:
        image = bpy.data.images.new("UV_Checker",2048,2048); image.generated_type = "COLOR_GRID"
    for o in objects:
        mat = bpy.data.materials.new("Review_" + o.name); mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = colours[int(o.get("zone",0))] if zones else colours[0]
        bsdf.inputs["Roughness"].default_value = .8
        if checker:
            tex = mat.node_tree.nodes.new("ShaderNodeTexImage");tex.image = image
            mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
        o.data.materials.clear();o.data.materials.append(mat)
        for f in o.data.polygons:f.material_index = 0
    points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    lo = Vector([min(v[i] for v in points) for i in range(3)])
    hi = Vector([max(v[i] for v in points) for i in range(3)])
    centre = (lo+hi)/2; span = max(hi-lo)
    cam = bpy.data.objects.new("ReviewCam",bpy.data.cameras.new("ReviewCam"));scene.collection.objects.link(cam)
    scene.camera = cam;cam.data.type = "ORTHO"
    for view in views:
        az,el = {"quarter":(-55,15),"pod_side":(-90,0),"opposite":(90,0),"front":(0,0),"back":(180,0),"top":(0,89)}[view]
        a,e = map(math.radians,(az,el));d = Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)))
        cam.location = centre+d*span*3;cam.rotation_euler = (-d).to_track_quat("-Z","Y").to_euler()
        rotation = cam.rotation_euler.to_matrix().transposed()
        projected = [rotation @ (v-centre) for v in points]
        width = max(v.x for v in projected)-min(v.x for v in projected)
        height = max(v.y for v in projected)-min(v.y for v in projected)
        cam.data.ortho_scale = max(width,height*1.5)*1.12
        scene.render.filepath = str(P/"review/geometry"/f"{prefix}_{view}.png")
        bpy.ops.render.render(write_still=True)


def make_parts():
    raw = P/"meshy/ion_cannon_geometry_v1/model_urls_glb.glb"
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==SOURCE_SHA
    bpy.ops.wm.open_mainfile(filepath=str(P/"work/ion_cannon_oriented_raw.blend"))
    obj = bpy.data.objects["IonCannon"]
    bm = bmesh.new();bm.from_mesh(obj.data)
    component = bm.faces.layers.int["source_component"]
    zone = bm.faces.layers.int.new("zone_id")
    # Meshy mirrored the near-side pod pair; retain the primary's -X flank only.
    duplicate_pods = {8,39,65,114,45,120,123,156}
    removed = [f for f in bm.faces if f[component] in duplicate_pods or f.calc_area()<1e-12]
    bmesh.ops.delete(bm,geom=removed,context="FACES")
    # The return has two broad muzzle jaws. Fit three narrower copies of its upper jaw to the approved front view.
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[component]==97],context="FACES")
    top = [f for f in bm.faces if f[component]==20]
    for v in {v for f in top for v in f.verts}:
        v.co.x = .0015+(v.co.x-.0015)*.55
    geom = list(set(top)|{e for f in top for e in f.edges}|{v for f in top for v in f.verts})
    for i,angle in enumerate((120,240),2001):
        result = bmesh.ops.duplicate(bm,geom=geom)["geom"]
        rotation = Matrix.Rotation(math.radians(angle),3,"Y")
        for v in result:
            if isinstance(v,bmesh.types.BMVert):
                v.co = Vector((.0015,0,-.018))+rotation @ (v.co-Vector((.0015,0,-.018)))
            elif isinstance(v,bmesh.types.BMFace):
                v[component] = i
    # Recessed resin liner closes the return's visible gaps between armour panels; silhouette stays with Meshy.
    rings=[]
    for y,z,rx,rz in [(.23,.025,.052,.055),(.05,.008,.057,.060),(-.08,0,.058,.055),
                      (-.18,-.008,.052,.051),(-.27,-.012,.047,.047),(-.36,-.017,.035,.038),
                      (-.425,-.018,.027,.029)]:
        rings.append([bm.verts.new((rx*math.cos(a),y,z+rz*math.sin(a)))
                      for a in np.linspace(0,2*math.pi,16,endpoint=False)])
    liner=[]
    for a,b in zip(rings,rings[1:]):
        for k in range(16):liner.append(bm.faces.new((a[k],a[(k+1)%16],b[(k+1)%16],b[k])))
    liner.extend([bm.faces.new(rings[0]),bm.faces.new(list(reversed(rings[-1])))])
    for f in liner:f[component]=3000
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update()
    cut = bm.faces.layers.int.new("cut_candidate")

    def patch(components, planes, target, front=lambda f:True):
        for f in bm.faces:f[cut] = int(f[component] in components and front(f))
        for point,normal in planes:
            faces = [f for f in bm.faces if f[cut]]
            if not faces:break
            geom = list(set(faces)|{e for f in faces for e in f.edges}|{v for f in faces for v in f.verts})
            bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-7,plane_co=point,plane_no=normal)
            for f in bm.faces:
                if f[cut] and (f.calc_center_median()-Vector(point)).dot(Vector(normal))>1e-7:f[cut]=0
        faces = [f for f in bm.faces if f[cut]]
        assert faces, (components,target)
        for f in faces:f[zone]=target

    def band(c,low,high,target):
        patch({c},[((0,low,0),(0,-1,0)),((0,high,0),(0,1,0))],target)

    for c,side in ((3,-1),(22,1)):
        planes = []
        for a in np.linspace(0,2*math.pi,16,endpoint=False):
            normal = (0,math.cos(a)/.042,math.sin(a)/.041)
            point = (0,.3045+.042*math.cos(a),.051+.041*math.sin(a))
            planes.append((point,normal))
        patch({c},planes,1,lambda f: f.normal.x*side>.3)
    band(16,.052,.207,2)
    patch({139},[((0,-.081,0),(0,-1,0)),((0,.148,0),(0,1,0)),
                 ((-.057,0,0),(1,0,0)),((0,0,-.024),(0,-.05,1))],2)
    for c,mid,target in [(26,-.0705,3),(54,-.1505,4),(24,-.2405,5),(70,-.334,6)]:
        band(c,mid-.008,mid+.008,target)
    patch({51},[((0,-.459,0),(0,1,0))],7)
    for c,angle in ((20,0),(2001,120),(2002,240)):
        outward = Matrix.Rotation(math.radians(angle),3,"Y") @ Vector((0,0,1))
        for f in bm.faces:
            if f[component]==c and f.normal.dot(outward)<-.25 and f.calc_center_median().y<-.435:
                f[zone]=7
    bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.calc_area()<1e-12],context="FACES")
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
    bm.to_mesh(obj.data);bm.free()
    parts = []
    for value,name in enumerate(ZONES):
        mesh = obj.data.copy();bm=bmesh.new();bm.from_mesh(mesh)
        layer = bm.faces.layers.int["zone_id"]
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f[layer]!=value],context="FACES")
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context="VERTS")
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
        bm.to_mesh(mesh);bm.free()
        o = bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(o);o["zone"]=value
        assert len(mesh.polygons)>0,name
        shade(o);parts.append(o)
    bpy.data.objects.remove(obj,do_unlink=True)
    report = {"source_sha256":SOURCE_SHA,"removed_mirrored_pod_components":sorted(duplicate_pods),
              "muzzle_correction":"Two broad jaws replaced by three narrowed copies of original upper jaw.",
              "gap_repair":"Recessed 16-sided resin liner behind barrel armour, 220 triangles.",
              "zone_triangles":{o.name:tris([o]) for o in parts},"total":tris(parts)}
    (P/"review/geometry/split.json").write_text(json.dumps(report,indent=2)+"\n")
    bpy.ops.wm.save_as_mainfile(filepath=str(P/"work/ion_cannon_parts.blend"))


def study():
    make_parts()
    rows=[]
    for ratio in (1,.8,.6,.4):
        bpy.ops.wm.open_mainfile(filepath=str(P/"work/ion_cannon_parts.blend"))
        parts=[o for o in bpy.context.scene.objects if o.type=="MESH"]
        body=next(o for o in parts if o["zone"]==0);select([body])
        if ratio<1:
            from mathutils.kdtree import KDTree
            points=[v.co.copy() for o in parts if o["zone"] for v in o.data.vertices]
            tree=KDTree(len(points))
            for i,point in enumerate(points):tree.insert(point,i)
            tree.balance()
            pinned=[v.index for v in body.data.vertices if tree.find(v.co)[2]<1e-7]
            group=body.vertex_groups.new(name="ReductionWeight")
            group.add(list(range(len(body.data.vertices))),1.0,"REPLACE");group.add(pinned,0.0,"REPLACE")
            original=[body.data.vertices[i].co.copy() for i in pinned]
            modifier=body.modifiers.new("Reduce","DECIMATE");modifier.ratio=ratio;modifier.use_collapse_triangulate=True
            modifier.vertex_group=group.name;modifier.vertex_group_factor=1000
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            check=KDTree(len(body.data.vertices))
            for v in body.data.vertices:check.insert(v.co,v.index)
            check.balance()
            error=max(check.find(v)[2] for v in original)
            assert error<1e-7,(ratio,"Glow seam moved",error)
            body["pinned_glow_seam_vertices"]=len(pinned)
            body["glow_seam_error"]=error
        shade(body)
        tag=f"reduction_{round(ratio*100)}"
        bpy.ops.wm.save_as_mainfile(filepath=str(P/"work"/f"ion_cannon_{tag}.blend"))
        rows.append({"ratio":ratio,"triangles":tris(parts),"body":tris([body])})
        render(parts,tag)
    (P/"review/geometry/reduction.json").write_text(json.dumps(rows,indent=2)+"\n")
    bpy.ops.wm.open_mainfile(filepath=str(P/"work/ion_cannon_parts.blend"))
    render([o for o in bpy.context.scene.objects if o.type=="MESH"],"zones",("pod_side","front","opposite"),zones=True)


def uv(ratio):
    bpy.ops.wm.open_mainfile(filepath=str(P/"work"/f"ion_cannon_reduction_{round(ratio*100)}.blend"))
    parts=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    coords=np.array([v.co[:] for o in parts for v in o.data.vertices])
    low=coords[coords[:,2]<coords[:,2].min()+.02]
    centre=(low[:,:2].min(0)+low[:,:2].max(0))/2
    floor=coords[:,2].min()
    # Head spans one raw unit; 50 m preserves the approved giant-cannon scale without moving the map's anchor.
    duplicate_faces_removed={}
    for o in parts:
        before=(len(o.data.vertices),len(o.data.edges),len(o.data.polygons))
        o.data.validate(verbose=True,clean_customdata=False)
        assert (len(o.data.vertices),len(o.data.edges))==before[:2],o.name
        duplicate_faces_removed[o.name]=before[2]-len(o.data.polygons)
        for v in o.data.vertices:v.co=(v.co-Vector((centre[0],centre[1],floor)))*50
        assert not o.data.validate(clean_customdata=False)
        shade(o)
        if not o.data.uv_layers:o.data.uv_layers.new(name="UVMap")
    select(parts);bpy.ops.object.mode_set(mode="EDIT");bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=SHARP,island_margin=0,area_weight=0,scale_to_bounds=False)
    bpy.ops.uv.select_all(action="SELECT");bpy.ops.uv.seams_from_islands()
    bpy.ops.object.mode_set(mode="OBJECT")
    for o in parts:
        for edge in o.data.edges:
            if edge.use_edge_sharp:edge.use_seam=True
    # One pinched chart on the front fin overlaps after angle unwrap; give that triangle its own island.
    body=next(o for o in parts if o.name=="Opaque")
    pinched=[f for f in body.data.polygons if (f.center-Vector((.9788965,-20.602181,14.964305))).length<.001]
    assert len(pinched)==1,len(pinched)
    cut=set(pinched[0].edge_keys)
    for edge in body.data.edges:
        if edge.key in cut:edge.use_seam=True
    bpy.ops.object.mode_set(mode="EDIT");bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.unwrap(method="ANGLE_BASED",margin=0)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True,margin=.0021,margin_method="FRACTION",shape_method="CONCAVE")
    bpy.ops.uv.seams_from_islands();bpy.ops.object.mode_set(mode="OBJECT")
    for o in parts:
        mat=bpy.data.materials.new(o.name);mat.use_nodes=True;mat.use_backface_culling=True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.5,.5,.5,1)
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.8
        o.data.materials.clear();o.data.materials.append(mat)
        for f in o.data.polygons:f.material_index=0
    uvstats={}
    for o in parts:
        bm=bmesh.new();bm.from_mesh(o.data);layer=bm.loops.layers.uv.active
        uvstats[o.name]={"triangles":len(bm.faces),"hard_edges_without_seams":sum(not e.smooth and not e.seam for e in bm.edges),
                         "pinned_glow_seam_vertices":int(o.get("pinned_glow_seam_vertices",0)),
                         "glow_seam_error":float(o.get("glow_seam_error",0))}
        bm.free()
        assert uvstats[o.name]["hard_edges_without_seams"]==0,o.name
    coords=np.array([v.co[:] for o in parts for v in o.data.vertices])
    uvstats["bounds_metres"]={"min":coords.min(0).tolist(),"max":coords.max(0).tolist()}
    uvstats["duplicate_faces_removed"]=duplicate_faces_removed
    uvstats["scale"]=50;uvstats["raw_base_centre"]=centre.tolist();uvstats["raw_floor"]=float(floor)
    uvstats["muzzle_axis_blender_metres"]=[float((.0015-centre[0])*50),float((-.5-centre[1])*50),float((-.018-floor)*50)]
    uvstats["packing"]={"method":"ANGLE_BASED with Smart UV and hard-edge seams; shared atlas","per_island_margin_fraction":.0021,"nominal_inter_island_gutter_at_2k":8.6016}
    (P/"review/geometry/uv_blender_checks.json").write_text(json.dumps(uvstats,indent=2)+"\n")
    bpy.ops.wm.save_as_mainfile(filepath=str(P/"work/ion_cannon_uv.blend"))
    select(parts)
    bpy.ops.export_scene.gltf(filepath=str(P/"work/ion_cannon_zones.glb"),use_selection=True,
        export_format="GLB",export_yup=True,export_skins=False,export_animations=False,export_attributes=False)
    # Keep per-face zone provenance in the editable master; upload one neutral material for one shared texture set.
    bpy.ops.object.join();obj=bpy.context.view_layer.objects.active;obj.name=obj.data.name="IonCannon"
    neutral=bpy.data.materials.new("IonCannon_Neutral");neutral.use_nodes=True;neutral.use_backface_culling=True
    neutral.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.5,.5,.5,1)
    neutral.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.8
    obj.data.materials.clear();obj.data.materials.append(neutral)
    for f in obj.data.polygons:f.material_index=0
    uvdata=obj.data.uv_layers.active.data
    np.savez(P/"work/ion_cannon_uv_triangles.npz",positions=np.array([[obj.data.vertices[i].co[:] for i in f.vertices] for f in obj.data.polygons]),
        uv=np.array([[uvdata[i].uv[:] for i in f.loop_indices] for f in obj.data.polygons]),
        zones=np.array([x.value for x in obj.data.attributes["zone_id"].data]))
    bpy.ops.wm.save_as_mainfile(filepath=str(P/"work/ion_cannon_neutral_upload.blend"))
    bpy.ops.export_scene.gltf(filepath=str(P/"work/ion_cannon_neutral_upload.glb"),use_selection=True,
        export_format="GLB",export_yup=True,export_skins=False,export_animations=False,export_attributes=False)
    render([obj],"uv_checker",("quarter","opposite"),checker=True)
    print("UPLOAD",tris([obj]),flush=True)


args=sys.argv[sys.argv.index("--")+1:]
try:
    if args[0]=="study":study()
    elif args[0]=="uv":uv(float(args[1]))
    else:raise ValueError(args)
except Exception:
    import traceback
    traceback.print_exc()
    sys.stdout.flush();sys.stderr.flush();os._exit(1)
print("DONE",args,flush=True)
sys.stdout.flush();sys.stderr.flush()
os._exit(0)

