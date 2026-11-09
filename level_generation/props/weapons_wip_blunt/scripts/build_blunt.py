"""Closed component weapons; Blender background only. UV cells deliberately reuse unlit materials."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
OWN = {r['icon']: r for r in json.loads((P / 'ownership.json').read_text())}
PARTS = []


def uv(cell, u, v):
    return ((cell % 4 + .03 + .94 * u) / 4, 1 - (cell // 4 + .97 - .94 * v) / 4)


def mesh(name, verts, faces, cell, coords=None, smooth=False):
    m = bpy.data.meshes.new(name)
    m.from_pydata(verts, [], faces)
    m.update()
    bm = bmesh.new(); bm.from_mesh(m)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(m); bm.free()
    o = bpy.data.objects.new(name, m); bpy.context.collection.objects.link(o)
    m.materials.append(bpy.data.materials['weapon_atlas'])
    layer = m.uv_layers.new()
    for f in m.polygons:
        f.use_smooth = smooth and len(f.vertices) <= 4
        axes = sorted(range(3), key=lambda a: abs(f.normal[a]))[:2]
        for li in f.loop_indices:
            vi = m.loops[li].vertex_index
            if coords and len(f.vertices) <= 4:
                u, v = coords[vi]
                if max(coords[m.loops[k].vertex_index][0] for k in f.loop_indices) - min(coords[m.loops[k].vertex_index][0] for k in f.loop_indices) > .7:
                    u = 1 if u < .1 else u
            else:
                u, v = [(.5 + verts[vi][a]) for a in axes]
            layer.data[li].uv = uv(cell, max(0, min(1, u)), max(0, min(1, v)))
    PARTS.append(o)
    return o


def tube(name, points, radii, cell, sides=12):
    verts, coords, faces = [], [], []
    lengths = [0]
    for a, b in zip(points, points[1:]): lengths.append(lengths[-1] + (Vector(a) - Vector(b)).length)
    for k, (p, r) in enumerate(zip(points, radii)):
        axis = (Vector(points[min(k+1,len(points)-1)]) - Vector(points[max(0,k-1)])).normalized()
        right = axis.cross(Vector((0,0,1))).normalized()
        if right.length < .1: right = Vector((1,0,0))
        up = axis.cross(right).normalized()
        rx, rz = r if isinstance(r, tuple) else (r,r)
        for n in range(sides):
            a = 2*math.pi*n/sides
            verts.append(tuple(Vector(p)+right*(rx*math.cos(a))+up*(rz*math.sin(a))))
            coords.append((n/sides*2*math.pi*max(rx,rz)/.8,lengths[k]/.8))
    for k in range(len(points)-1):
        for n in range(sides):
            faces.append((k*sides+n,k*sides+(n+1)%sides,(k+1)*sides+(n+1)%sides,(k+1)*sides+n))
    faces += [tuple(reversed(range(sides))),tuple((len(points)-1)*sides+n for n in range(sides))]
    return mesh(name,verts,faces,cell,coords,True)


def shaft(y0,y1,r,cell,x=0,z=0):
    return tube('shaft',[(x,y0,z),(x,y1,z)],[r,r],cell)


def lathe(name, profile, cell, x=0, z=0, sides=16):
    return tube(name,[(x,y,z) for y,r in profile],[r for y,r in profile],cell,sides)


def ball(c,r,cell,sub=2):
    bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=sub,radius=1);bm.verts.ensure_lookup_table()
    rs=(r,r,r) if isinstance(r,(float,int)) else r
    vs=[tuple(Vector(c)+Vector((v.co.x*rs[0],v.co.y*rs[1],v.co.z*rs[2]))) for v in bm.verts]
    coords=[(.5+math.atan2(v.co.z,v.co.x)/(2*math.pi),.5+math.asin(max(-1,min(1,v.co.y)))/math.pi) for v in bm.verts]
    o=mesh('solid head',vs,[[v.index for v in f.verts] for f in bm.faces],cell,coords,True);bm.free();return o


def box(c,size,cell,bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.name='bevelled solid forging';o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('edge bevel','BEVEL');mod.width=bevel;mod.segments=1;bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.append(bpy.data.materials['weapon_atlas']);layer=o.data.uv_layers.active or o.data.uv_layers.new()
    for f in o.data.polygons:
        axes=sorted(range(3),key=lambda a:abs(f.normal[a]))[:2]
        for li in f.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co
            layer.data[li].uv=uv(cell,*[max(0,min(1,co[a]/.8+.5)) for a in axes])
    PARTS.append(o);return o


def spike(a,b,r,cell):
    return tube('tapered solid spike',[a,b],[r,.0018],cell,6)


def ring(c,r,cell,normal=(0,1,0),wire=.009,ratio=1):
    axis=Vector(normal).normalized();right=axis.cross(Vector((0,0,1))).normalized()
    if right.length<.1:right=Vector((1,0,0))
    up=axis.cross(right);vs=[];coords=[];faces=[]
    for n in range(8):
        a=n*2*math.pi/8;radial=right*math.cos(a)+up*math.sin(a)
        for k in range(4):
            b=k*2*math.pi/4
            vs.append(tuple(Vector(c)+right*(r*math.cos(a))+up*(r*ratio*math.sin(a))+radial*(wire*math.cos(b))+axis*(wire*math.sin(b))))
            coords.append((n/8,k/4))
    for n in range(8):
        for k in range(4):faces.append((n*4+k,((n+1)%8)*4+k,((n+1)%8)*4+(k+1)%4,n*4+(k+1)%4))
    return mesh('forged closed link',vs,faces,cell,coords,True)


def chain(points,cell=0):
    for i,p in enumerate(points):ring(p,.019,cell,(0,0,1) if i%2 else (1,0,0),.006,1.45)


def grip(cell=3,metal=0,wood=2,y0=-.48,y1=.3,r=.024,style='plain'):
    shaft(y0,y1,r,wood)
    shaft(y0+.025,y0+.31,r*1.2,cell)
    for y in [y0,y0+.025,y0+.31,y1]:lathe('collar',[(y-.008,r*1.34),(y+.008,r*1.34)],metal)
    ball((0,y0-.006,0),(r*1.15,.018,r*1.15),metal,1)
    if style=='twist':
        pts=[(.024*math.cos(i*.55),y0+.34+i*(y1-y0-.35)/40,.024*math.sin(i*.55)) for i in range(41)]
        tube('raised spiral handle',pts,[.008]*len(pts),metal,5)
    elif style=='bands':
        for n in range(5):lathe('shaft rings',[(y0+.36+n*.08,.029),(y0+.374+n*.08,.029)],metal)


def star(c,r,cell,mode='spikes',count=6):
    ball(c,r,cell,3)
    for n in range(count):
        a=n*2*math.pi/count;x,y,z=c
        if mode=='studs':ball((x+math.cos(a)*r*.88,y,z+math.sin(a)*r*.88),r*.37,cell,2)
        else:spike((x+math.cos(a)*r*.75,y,z+math.sin(a)*r*.75),(x+math.cos(a)*r*1.7,y,z+math.sin(a)*r*1.7),r*.31,cell)
    if mode!='studs':spike((c[0],c[1]+r*.6,c[2]),(c[0],c[1]+r*1.7,c[2]),r*.3,cell)


def flange(y,cell,r=.1,h=.22,count=6):
    shaft(y-h*.5,y+h*.5,r*.37,cell)
    profile=[(-h*.5,r*.3),(-h*.3,r*.8),(0,r),(h*.35,r*.7),(h*.5,r*.25)]
    for n in range(count):
        a=n*2*math.pi/count;verts=[]
        for side in [-1,1]:
            for yy,rr in profile:verts.append((rr*math.cos(a)-side*.008*math.sin(a),y+yy,rr*math.sin(a)+side*.008*math.cos(a)))
        faces=[tuple(range(4,-1,-1)),tuple(range(5,10))]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
        mesh('thick radial flange',verts,faces,cell)
    for yy in [y-h*.5,y+h*.5]:lathe('head socket',[(yy-.012,r*.46),(yy+.012,r*.46)],cell)


def flail(icon):
    cell=1 if icon=='7item230' else 0
    number={'7item053':1,'7item054':2,'7item230':3,'item067':2}[icon]
    wood=8 if icon=='7item054' else 3 if icon=='item067' else 2
    grip(4 if icon=='7item230' else 3,1 if icon=='7item054' else cell,wood,y1=.40,r=.027)
    lathe('upper flail ferrule',[(.37,.037),(.44,.037),(.47,.025)],cell)
    radius=.074 if number>1 else .095
    handle_height=-radius+.034
    for o in PARTS:o.location.z=handle_height
    for n in range(number):
        hx=-.18-n*.10;hy=.13-n*.20;r=.074 if number>1 else .095
        pts=[]
        count=round((.47-hy)/.034)+2
        for k in range(count):
            t=k/(count-1)
            floor_height=-r+(.028 if k%2==0 else .009)
            z=handle_height*(1-t) if t<.2 or t>.8 else floor_height
            pts.append((hx*t,.44+(hy-.44)*t,z))
        chain(pts,cell);star((hx,hy-r,.0),r,cell,'studs' if icon=='item067' else 'spikes',6)


def hammer(icon):
    styles={
        'item073':('pick',1,7,4), 'item072':('field',0,2,3), '7item056':('pick',8,2,3),
        '7item057':('fan',0,0,8),'item074':('sun',1,7,7),'7item231':('sun',1,1,1),
        'item071':('block',8,1,1),'7item055':('block',8,2,4),'hammer1':('block',8,2,3),
        'item075':('layer',8,5,13),'6hammer4':('moon',0,7,8),'hammer3':('moon',0,7,8),
        'hammer2':('crescent',8,7,7)}
    style,metal,wood,leather=styles[icon]
    grip(leather,1 if icon in ['item073','item071','item074','7item231','item075','6hammer4','hammer3'] else 0,wood,y1=.34,r=.024,style='twist' if icon in ['item071','7item231'] else 'plain')
    y=.34
    if style in ['block','layer']:
        width=.46 if icon=='item071' else .33
        box((0,y,0),(width,.18,.15),metal,.013)
        box((0,y,0),(.055,.21,.172),1 if icon!='7item055' else 0)
        if style=='layer':
            for yy in [y-.064,y,y+.064]:box((0,yy,0),(.36,.024,.16),8,.004)
        if icon in ['7item055','hammer1','item071']:chain([(0,-.51-k*.028,0) for k in range(4)])
    elif style in ['pick','field','fan','sun']:
        box((0,y,0),(.075,.095,.08),metal)
        # Separate curved pick and substantial striking body, not a flat extruded icon.
        side=-1 if icon=='item073' else 1
        pts=[(side*.033,y,0),(side*.10,y+.015,0),(side*.18,y-.015,0),(side*.23,y-.06,0)]
        if style=='field':pts=[(.03,y,0),(.11,y,0),(.18,y-.015,0)]
        tube('curved tapered pick',pts,[.026,.023,.014,.002] if len(pts)==4 else [.024,.018,.002],metal,8)
        x=-side
        tube('hammer striking body',[(x*.025,y,0),(x*.12,y,0),(x*.17,y,0)],[.024,.036,.056],metal,12)
        if style in ['fan','sun']:
            for n in range(5):
                yy=y+(n-2)*.022
                tube('fluted striking face',[(x*.06,y,0),(x*.17,yy,0)],[.01,.012],metal,6)
        spike((0,y+.045,0),(0,y+.17,0),.026,metal)
        box((0,y,.046),(.037,.047,.012),1 if style in ['sun','fan'] else 8,.002)
    elif style=='moon':
        box((0,y,0),(.085,.085,.075),1)
        tube('gold hammer end',[(-.04,y,0),(-.15,y,0)],[.035,.052],1)
        # Crescent is a curved solid wedge with an inner cutting arc.
        outline=[(.15,y+.16),(.12,y+.12),(.10,y+.06),(.095,y),(.10,y-.06),(.12,y-.12),(.15,y-.16),(.07,y-.11),(.045,y-.06),(.038,y),(.045,y+.06),(.07,y+.11)]
        vs=[(x,yy,z) for z in [-.021,.021] for x,yy in outline];n=len(outline)
        mesh('solid crescent blade',vs,[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],0)
        for x in [-.028,.028]:box((x,y,.044),(.018,.048,.015),6,.002)
        box((0,y,.049),(.024,.027,.018),4,.002)
    elif style=='crescent':
        tube('sweeping hammer arc',[(-.20,y-.035,0),(-.12,y+.005,0),(0,y+.015,0),(.12,y+.005,0),(.20,y-.035,0)],[.015,.026,.031,.026,.015],metal,10)
        spike((0,y+.025,0),(0,y+.20,0),.032,0)


def mace(icon):
    metal=1 if icon in ['item068','item340','item069','mace4','7item232','item249'] else 0
    handle={'item066':11,'7item050':2,'7item051':2,'7item052':8,'item068':3,'item340':3,'item069':4,'item070':8,'mace1':15,'mace2':2,'mace3':13,'mace4':1,'7item232':4,'item249':5}[icon]
    grip(handle,metal,handle,y1=.30,r=.022,style='bands' if icon in ['item070','mace1','mace3'] else 'plain')
    if icon in ['item066','7item050','7item051','mace1','mace2','mace4']:
        r=.085 if icon not in ['mace2'] else .06
        if icon=='mace2':
            ball((0,.36,0),(.060,.043,.060),0,3)
            lathe('head equatorial band',[(.35,.063),(.37,.063)],0)
            spike((0,.39,0),(0,.59,0),.025,0)
            chain([(0,-.52-n*.03,0) for n in range(4)])
        else:star((0,.36,0),r,metal,'spikes' if icon=='7item051' else 'studs',6 if icon!='7item050' else 8)
        if icon=='mace4':
            for a in range(4):ball((.07*math.cos(a*math.pi/2),.36,.07*math.sin(a*math.pi/2)),.025,6,1)
            box((0,-.37,.029),(.04,.07,.012),6,.002)
        if icon=='mace1':box((0,-.48,0),(.042,.045,.042),6,.004)
    elif icon=='item249':
        ball((0,.37,0),(.084,.10,.084),4)
        for n in range(6):
            a=n*math.pi/3
            pts=[(.083*math.sin(t*math.pi)*math.cos(a),.275+t*.19,.083*math.sin(t*math.pi)*math.sin(a)) for t in [.05,.2,.4,.6,.8,.95]]
            tube('crown rib',pts,[.008]*len(pts),1,5)
        ball((0,.48,0),.021,1,1)
    elif icon=='item069':
        shaft(.26,.49,.018,metal)
        for y in [.28,.32,.36,.40,.44]:
            for n in range(6):
                a=n*math.pi/3;spike((.014*math.cos(a),y,.014*math.sin(a)),(.047*math.cos(a),y,.047*math.sin(a)),.009,metal)
        spike((0,.49,0),(0,.60,0),.022,metal)
    elif icon=='7item232':
        flange(.30,1,.075,.36,6)
        for y in [.16,.24,.32,.40]:
            for s in [-1,1]:spike((s*.052,y,0),(s*.10,y,.0),.016,1)
        spike((0,.48,0),(0,.61,0),.025,1)
    else:
        r=.11 if icon in ['item068','item340'] else .09
        flange(.35,metal,r,.24,6)
        spike((0,.47,0),(0,.60,0),.023,metal)
        if icon in ['7item052','mace3','item070','item068','item340']:
            for n in range(4):
                a=n*math.pi/2;spike((r*.7*math.cos(a),.35,r*.7*math.sin(a)),(r*1.6*math.cos(a),.35,r*1.6*math.sin(a)),.025,metal)
        if icon in ['item068','item340']:
            pts=[(.025*math.cos(i*.6),-.44+i*.045,.025*math.sin(i*.6)) for i in range(8)]
            tube('ivory spiral foot',pts,[.01]*8,5,5)


def club(icon):
    if icon=='club3':
        grip(7,1,7,y1=.34,r=.024)
        shaft(.10,.57,.018,0)
        for y,w in [(.12,.07),(.30,.085),(.48,.072),(.60,.042)]:
            box((0,y,0),(w,.066,w),10,.012)
            box((0,y,.047),(.025,.035,.016),1,.004)
    elif icon=='7item060':
        grip(8,0,8,y1=.37,r=.021,style='bands')
        for y,r in [(.18,.046),(.25,.074),(.33,.089),(.41,.066)]:
            lathe('solid steel club tier',[(y-.021,r*.7),(y-.01,r),(y+.01,r),(y+.021,r*.7)],0)
        spike((0,.43,0),(0,.59,0),.024,0)
    elif icon=='7item059':
        grip(8,0,8,y1=.20,r=.022)
        lathe('elongated iron club',[(.10,.033),(.16,.048),(.30,.058),(.44,.043),(.50,.019)],8)
        for y in [.17,.26,.35,.44]:
            for n in range(4):
                a=n*math.pi/2+(y-.17)*2
                spike((.044*math.cos(a),y,.044*math.sin(a)),(.10*math.cos(a),y+.012,.10*math.sin(a)),.014,0)
        spike((0,.49,0),(0,.63,0),.022,0)
    elif icon=='item076':
        grip(3,0,8,y1=.47,r=.018)
        for y in [.20,.25,.30,.35,.40,.45]:
            for n in range(4):
                a=n*math.pi/2
                spike((.015*math.cos(a),y,.015*math.sin(a)),(.068*math.cos(a),y+.009,.068*math.sin(a)),.010,0)
        spike((0,.47,0),(0,.57,0),.019,0)
        chain([(0,-.52-i*.032,0) for i in range(4)])
    elif icon=='item078':
        grip(3,1,11,y1=.26,r=.025)
        lathe('tapered bronze club',[(0,.031),(.15,.057),(.32,.080),(.49,.068)],14)
        for y,r in [(.06,.043),(.19,.063),(.32,.083),(.47,.074)]:
            lathe('iron reinforcing band',[(y-.014,r),(y+.014,r)],8)
        for y in [.31,.42]:
            for n in range(4):
                a=n*math.pi/2
                spike((.06*math.cos(a),y,.06*math.sin(a)),(.115*math.cos(a),y,.115*math.sin(a)),.016,0)
        spike((0,.49,0),(0,.57,0),.028,0)
    else:raise AssertionError(icon)


def finish(icon):
    # Two actual support radii determine the resting handle angle.
    non_chain=[o for o in PARTS if o.name.split('.')[0]!='forged closed link']
    points=[o.matrix_world@v.co for o in non_chain for v in o.data.vertices]
    front=[p.z for p in points if p.y>.15];back=[p.z for p in points if p.y<-.3]
    slope=(abs(min(front))-abs(min(back)))/.72 if front and back else 0
    if icon not in ['7item053','7item054','7item230','item067']:
        for o in PARTS:
            o.rotation_mode='XYZ';o.rotation_euler.x=math.atan(slope)
    bpy.context.view_layer.update()
    coords=[o.matrix_world@v.co for o in PARTS for v in o.data.vertices]
    lo=Vector([min(p[a] for p in coords) for a in range(3)]);hi=Vector([max(p[a] for p in coords) for a in range(3)])
    scale=1/max(hi.x-lo.x,hi.y-lo.y);center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
    for o in PARTS:
        matrix=o.matrix_world.copy()
        for v in o.data.vertices:v.co=(matrix@v.co-center)*scale
        o.matrix_world.identity()
        # Natural component seams coincide with all hard boundaries.
        for e in o.data.edges:e.use_seam=True
    bpy.ops.object.select_all(action='DESELECT')
    for o in PARTS:o.select_set(True)
    bpy.context.view_layer.objects.active=PARTS[0];bpy.ops.object.join();o=bpy.context.object
    mod=o.modifiers.new('deterministic triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
    assert 100<len(o.data.polygons)<15000,(icon,len(o.data.polygons))
    assert min(v.co.z for v in o.data.vertices)>-1e-6
    out=P/'work/blender'/f'{icon}_export.glb'
    bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_yup=True,export_texcoords=True,export_normals=True,export_materials='EXPORT')
    entry={'icon':icon,'triangles':len(o.data.polygons),'vertices':len(o.data.vertices),'export':str(out.relative_to(P)),'route':'authored Blender components + imagegen UV atlas','texture_size':1024}
    (P/'work/blender'/f'{icon}.json').write_text(json.dumps(entry,indent=2)+'\n')
    return entry


def material():
    m=bpy.data.materials.new('weapon_atlas');m.use_nodes=True;m.use_backface_culling=True
    nt=m.node_tree;s=nt.nodes.get('Principled BSDF')
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'textures/material_albedo.png'));nt.links.new(t.outputs['Color'],s.inputs['Base Color'])
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'textures/material_orm.png'));t.image.colorspace_settings.name='Non-Color'
    separate=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(t.outputs['Color'],separate.inputs[0]);nt.links.new(separate.outputs['Green'],s.inputs['Roughness']);nt.links.new(separate.outputs['Blue'],s.inputs['Metallic'])
    t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'textures/material_normal.png'));t.image.colorspace_settings.name='Non-Color'
    normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(t.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],s.inputs['Normal'])


def main():
    args=sys.argv[sys.argv.index('--')+1:]
    for icon in args:
        assert icon in OWN
        bpy.ops.wm.read_factory_settings(use_empty=True);PARTS.clear();material()
        if icon in ['7item053','7item054','7item230','item067']:flail(icon)
        elif icon in ['item073','item072','7item056','7item057','item074','7item231','item071','7item055','hammer1','item075','6hammer4','hammer3','hammer2']:hammer(icon)
        elif icon in ['club3','7item060','7item059','item076','item078']:club(icon)
        else:mace(icon)
        print('BUILT',json.dumps(finish(icon)))


if __name__=='__main__':main()
