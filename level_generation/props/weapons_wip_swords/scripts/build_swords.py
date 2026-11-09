"""Physical blade sections and independently authored hilts, in isolated Blender.

blender --background --factory-startup --python build_swords.py -- [icon ...]
"""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
MATERIALS={}
SCALE=1
H=1
CX=0
G=0


def point(x,y,z=0):
    return Vector(((x-CX)*SCALE,(H-y)*SCALE,z))


def material(name):
    if name in MATERIALS:return MATERIALS[name]
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=True
    tree=mat.node_tree;shader=tree.nodes.get('Principled BSDF')
    for suffix in ('base','mr','normal'):
        tex=tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(PROJECT/'textures'/f'{name}_{suffix}.png'),check_existing=True)
        if suffix=='base':tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
        elif suffix=='mr':
            tex.image.colorspace_settings.name='Non-Color'
            split=tree.nodes.new('ShaderNodeSeparateColor');tree.links.new(tex.outputs['Color'],split.inputs['Color'])
            tree.links.new(split.outputs['Green'],shader.inputs['Roughness']);tree.links.new(split.outputs['Blue'],shader.inputs['Metallic'])
        else:
            tex.image.colorspace_settings.name='Non-Color'
            normal=tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.7
            tree.links.new(tex.outputs['Color'],normal.inputs['Color']);tree.links.new(normal.outputs['Normal'],shader.inputs['Normal'])
    MATERIALS[name]=mat
    return mat


def uv_project(obj):
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.uv_layers.active.name='UVMap'


def mesh(name,vertices,faces,mat,smooth=False):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
    bm=bmesh.new();bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='SHORT_EDGE',ngon_method='EAR_CLIP')
    assert all(edge.is_manifold for edge in bm.edges),name
    assert all(face.calc_area()>1e-12 for face in bm.faces),name
    bm.to_mesh(data);bm.free()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    data.materials.append(material(mat))
    for poly in data.polygons:poly.use_smooth=smooth
    uv_project(obj)
    return obj


def sphere(name,x,y,size,mat,z=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=point(x,y,z))
    obj=bpy.context.object;obj.name=name;obj.scale=tuple(v*SCALE for v in size)
    obj.data.materials.append(material(mat))
    for poly in obj.data.polygons:poly.use_smooth=True
    uv_project(obj)
    return obj


def tube(name,points,radius,mat,taper=False,sides=8):
    points=[Vector(p) for p in points];verts=[];n=len(points)
    for i,p in enumerate(points):
        tangent=(points[min(i+1,n-1)]-points[max(i-1,0)]).normalized()
        axis=tangent.cross(Vector((0,0,1)))
        if axis.length<.01:axis=tangent.cross(Vector((0,1,0)))
        axis.normalize();other=tangent.cross(axis)
        r=radius*(max(.13,1-i/(n-1)) if taper else 1)
        for j in range(sides):verts.append(p+r*(axis*math.cos(math.tau*j/sides)+other*math.sin(math.tau*j/sides)))
    faces=[]
    for i in range(n-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple((n-1)*sides+j for j in range(sides))])
    return mesh(name,verts,faces,mat,True)


def path(name,xy,radius,mat,taper=False,z=0):
    if name in ('Open knuckle bow','Organic guard tine'):
        source=[Vector(p) for p in xy];smooth=[]
        for i in range(len(source)-1):
            a=source[max(0,i-1)];b=source[i];c=source[i+1];d=source[min(len(source)-1,i+2)]
            for t in (0,.25,.5,.75):
                smooth.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
        xy=smooth+[tuple(source[-1])]
    return tube(name,[point(x,y,z) for x,y in xy],radius*SCALE,mat,taper)


def lathe(name,x,y0,y1,profile,mat,radius):
    sides=12;vertices=[]
    for t,r in profile:
        for j in range(sides):
            a=math.tau*j/sides;vertices.append(point(x+radius*r*math.cos(a),y0+(y1-y0)*t,radius*r*math.sin(a)*SCALE))
    faces=[]
    for i in range(len(profile)-1):
        for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple((len(profile)-1)*sides+j for j in range(sides))])
    obj=mesh(name,vertices,faces,mat,True)
    # Unrolled cylindrical walls give grain and ornament a consistent direction.
    uv=obj.data.uv_layers.active.data
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            index=obj.data.loops[li].vertex_index;ring,j=divmod(index,sides)
            uv[li].uv=(.02+.96*j/sides,.02+.96*profile[ring][0])
        if len({round(uv[li].uv.y,6) for li in poly.loop_indices})==1:
            for li in poly.loop_indices:
                v=obj.data.vertices[obj.data.loops[li].vertex_index].co
                uv[li].uv=(.5+(v.x-(x-CX)*SCALE)/(radius*SCALE)*.46,.5+v.z/(radius*SCALE)*.46)
        elif max(uv[li].uv.x for li in poly.loop_indices)-min(uv[li].uv.x for li in poly.loop_indices)>.5:
            for li in poly.loop_indices:
                if uv[li].uv.x<.1:uv[li].uv.x=.98
    return obj


def leaf(name,start,end,width,mat,depth=2):
    a,b=Vector(start),Vector(end);axis=(b-a).normalized();side=Vector((-axis.y,axis.x));verts=[]
    shape=[(0,.035),(.25,.7),(.6,1),(.9,.45),(1,.025)]
    for t,w in shape:
        c=a+(b-a)*t
        for lateral,z in ((-w,0),(0,w),(w,0),(0,-w)):
            verts.append(point(*(c+side*width*lateral),z*depth*SCALE))
    faces=[]
    for i in range(len(shape)-1):
        for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    faces.extend([tuple(reversed(range(4))),tuple((len(shape)-1)*4+j for j in range(4))])
    return mesh(name,verts,faces,mat)


def blade(config):
    if 'fork_branches_px' in config:
        for branch in config['fork_branches_px']:
            part={k:v for k,v in config.items() if k!='fork_branches_px'}
            part['blade_outline_px']=branch
            blade(part)
    outline=config['blade_outline_px'];verts=[]
    # The edge is 0.45 mm, the ridge 5–7 mm: a forged blade, not an inflated silhouette.
    thick=.0032 if 'Two' not in config['title'] else .004
    single=config['guard'] in ('d_left','d_right','shell','scroll_bow','ornate_bow','horn_bow','skull_scroll','dragon_small')
    fuller=config['master_icon'] in ('item002','item004','item009','item010','item334','item342','lsword2','7item006','item006','lsword1')
    profile=[(-1,.00023),(-.55,thick),(-.20,thick*.70),(0,thick*.70),(.20,thick*.70),(.55,thick),(1,.00023)] if fuller else [(-1,.00023),(-.30,thick),(.30,thick),(1,.00023)]
    if single:profile=[(-1,.00023),(.20,thick),(.78,thick),(1,thick*.35)]
    section=profile+[(x,-z) for x,z in reversed(profile)];count=len(section)
    for y,left,right in outline:
        half=(right-left)/2;centre=(right+left)/2
        for x,z in section:verts.append(point(centre+x*half,y,z))
    faces=[]
    for i in range(len(outline)-1):
        for j in range(count):faces.append((i*count+j,i*count+(j+1)%count,(i+1)*count+(j+1)%count,(i+1)*count+j))
    faces.extend([tuple(reversed(range(count))),tuple((len(outline)-1)*count+j for j in range(count))])
    mat={'bronze':'warmsteel','gold':'gold_blade'}.get(config['blade_material'],config['blade_material'])
    obj=mesh('Forged blade — bevels and '+('fuller' if fuller else 'ridge'),verts,faces,mat)
    # Broad front/back faces have a lengthwise, unlit material, never icon projection.
    uv=obj.data.uv_layers.active.data
    for poly in obj.data.polygons:
        if abs(poly.normal.z)>.25:
            for li in poly.loop_indices:
                v=obj.data.vertices[obj.data.loops[li].vertex_index].co
                uv[li].uv=(.5+v.x/1.5,.03+v.y/1.5*.94)
    return obj


def gem(x,y,r,colour='ruby',z=None):
    return sphere('Set '+colour,x,y,(r,r*.78,r*.40),colour,z if z is not None else r*SCALE*.75)


def skull(x,y,r,metal):
    sphere('Sculpted cranium',x,y,(r*.80,r,r*.56),metal)
    sphere('Jaw',x,y+r*.75,(r*.57,r*.40,r*.42),metal)
    for sign in (-1,1):
        # Inset dark eye sockets sit under projecting brows on both visible faces.
        for face in (-1,1):
            sphere('Eye socket',x+sign*r*.32,y-r*.1,(r*.22,r*.28,r*.12),'black',face*r*SCALE*.51)
        sphere('Cheekbone',x+sign*r*.62,y+r*.36,(r*.3,r*.35,r*.42),metal)


def guard(config):
    kind=config['guard'];metal=config['metal_material'];w=config['size_px'][0]
    x=CX;y=G;span=w*.45;h=H;small=h*.008
    if kind in ('plain','disc','ribbed'):
        if kind=='disc':lathe('Elliptic rain guard',x,y-small,y+small,[(0,.8),(.25,1),(.75,1),(1,.8)],metal,span*.65)
        else:
            path('Crossguard',[(x-span,y-2),(x-span*.8,y),(x,y+1),(x+span*.8,y),(x+span,y-2)],small*1.0,metal)
            for s in (-1,1):sphere('Quillon finial',x+s*span,y-2,(small*1.4,small*1.4,small*1.5),metal)
    elif kind in ('d_left','d_right','shell','scroll_bow','horn_bow','ornate_bow'):
        direction=1 if kind=='d_right' else -1
        path('Crossguard',[(x-span*.8,y),(x,y),(x+span*.8,y)],small,metal)
        path('Open knuckle bow',[(x+direction*span*.25,y),(x+direction*span*.75,y+h*.025),
             (x+direction*span,y+h*.075),(x+direction*span*.91,y+h*.135),
             (x+direction*span*.57,y+h*.18),(x,y+h*.20)],small*.75,metal)
        if kind=='shell':
            leaf('Solid scalloped shell',(x,y),(x-span*.83,y+h*.095),span*.29,'feather',small*1.2)
            for i in range(7):
                leaf('Fluted shell lobe',(x,y),(x-span*(.35+.10*i),y+h*(.035+.014*i)),small*1.3,'feather',small*.65)
        if kind in ('scroll_bow','horn_bow','ornate_bow'):
            for s in (-1,1):
                path('Swept horn',[(x,y),(x+s*span*.6,y-2),(x+s*span*.9,y-h*.04),(x+s*span*.7,y-h*.07)],small,metal,True)
        if kind=='ornate_bow':gem(x,y,small*2.5)
    elif kind in ('angular','double_fork','v_guard','claymore','open_guard','scroll','crescent','skull_arch','horns','twisted_horns','serpents'):
        for s in (-1,1):
            if kind in ('angular','double_fork','open_guard'):
                xy=[(x,y),(x+s*span*.55,y),(x+s*span*.95,y-h*.07),(x+s*span*.82,y-h*.10)]
            elif kind in ('scroll','horns','twisted_horns','serpents'):
                xy=[(x,y),(x+s*span*.65,y),(x+s*span*.95,y-h*.018),(x+s*span,y-h*.045),
                    (x+s*span*.84,y-h*.055),(x+s*span*.72,y-h*.04)]
                if kind in ('horns','twisted_horns','serpents'):xy=xy[:3]+[(x+s*span*.95,y-h*.09),(x+s*span*.77,y-h*.15)]
            elif kind=='skull_arch':xy=[(x,y-h*.012),(x+s*span*.42,y),(x+s*span*.8,y+h*.03),(x+s*span,y+h*.09)]
            elif kind=='crescent':xy=[(x,y),(x+s*span*.45,y-h*.005),(x+s*span*.8,y-h*.035),(x+s*span,y-h*.06)]
            else:xy=[(x,y),(x+s*span*.45,y-h*.025),(x+s*span*.95,y-h*.065)]
            path('Left/right shaped quillon',xy,small*(1.15 if kind=='angular' else .9),metal,kind in ('horns','twisted_horns','serpents','skull_arch'))
            if kind in ('v_guard','claymore'):sphere('Quillon terminal',*xy[-1],(small*1.5,small*1.5,small*1.2),metal)
            if kind=='double_fork':path('Secondary crossguard',[(a,b+h*.18) for a,b in xy],small,metal)
        if kind=='skull_arch':skull(x,y,small*3,'bone')
        if kind=='serpents':
            skull(x,y+h*.19,small*2.4,'bone')
            for i in range(5):leaf('Serpent foliage',(x,y+h*.20),(x+math.cos(i*2.4)*span*.65,y+h*(.24+.02*math.sin(i))),small*1.2,'greensteel',small*.6)
    elif kind in ('angel','feather','antlers','thorns','crown','dragon','dragon_small','bat','bone','skulls','skull_scroll','candles','cup','artifact_collar'):
        reach=.9 if kind=='candles' else .55
        path('Crossguard core',[(x-span*reach,y),(x,y+small),(x+span*reach,y)],small*1.4,metal)
        if kind in ('angel','feather'):
            for s in (-1,1):
                for i in range(6):
                    leaf('Swept feather',(x+s*small*(.2+i*.45),y),
                         (x+s*span*(.40+i*.12),y-h*(.018+i*.012)),small*(1.3-i*.10),'feather',small*.65)
            if kind=='feather':
                for s in (-1,1):path('Wing crown',[(x,y),(x+s*span*.6,y-h*.04),(x+s*span*.5,y-h*.10),(x,y-h*.13)],small*.5,metal)
        elif kind in ('antlers','crown','thorns'):
            for s in (-1,1):
                for i in range(3):
                    path('Organic guard tine',[(x,y),(x+s*span*(.35+.2*i),y-h*.012),
                         (x+s*span*(.48+.23*i),y-h*(.03+.018*i)),
                         (x+s*span*(.40+.27*i),y-h*(.045+.022*i))],small*1.4,metal,True)
            if kind=='thorns':
                for i in range(3):
                    leaf('Thorned rain guard',(x,y),(x+(-1)**i*span*.25,y-h*(.05+.04*i)),small*1.5,metal,small*.6)
        elif kind in ('dragon','dragon_small'):
            for s in (-1,1):
                path('Dragon neck',[(x,y),(x+s*span*.55,y-h*.018),(x+s*span*.75,y-h*.05)],small*1.8,metal)
                skull(x+s*span*.75,y-h*.05,small*1.7,metal)
                path('Dragon horn',[(x+s*span*.7,y-h*.06),(x+s*span*.95,y-h*.085)],small*.75,metal,True)
            if kind=='dragon':
                leaf('Dragon spine',(x,y),(x,y-h*.18),small*3.2,'silver',small)
                for i in range(3):gem(x,y-h*(.025+i*.04),small,'cyan')
        elif kind in ('bone','skulls','skull_scroll'):
            if kind=='skull_scroll':skull(x,y,small*2.3,metal)
            else:
                for s in (-1,1):
                    path('Bone quillon',[(x,y),(x+s*span*.65,y-h*.008),(x+s*span*.88,y-h*.035)],small*1.4,metal)
                    skull(x+s*span*.82,y-h*.018,small*2.1,metal)
                if kind=='skulls':skull(x,y-h*.012,small*2.1,metal)
        elif kind=='bat':
            for s in (-1,1):
                leaf('Bat guard wing',(x,y),(x+s*span*.96,y-h*.04),small*2.5,metal,small)
        elif kind=='candles':
            for s in (-1,1):lathe('Candle quillon',x+s*span*.8,y-h*.12,y,[(0,.45),(.15,.6),(.85,.6),(1,1)],metal,small*1.5)
            sphere('Large ruby setting',x,y-h*.025,(small*5.2,small*4.4,small*2),metal,small*SCALE)
            gem(x,y-h*.025,small*4.8)
        elif kind=='cup':lathe('Pierced cup guard',x,y-h*.015,y+h*.04,[(0,1),(.2,1),(.85,.35),(1,.3)],metal,span*.7)
        if kind=='artifact_collar':
            lathe('Artifact collar',x,y-h*.014,y+h*.014,[(0,.85),(.3,1),(.7,1),(1,.85)],metal,span*.42)
            leaf('Raised sigil',(x,y-h*.025),(x+span*.38,y-h*.13),small*2.1,metal,small*.5)
    else:raise ValueError(kind)


def hilt(config):
    if config['master_icon']=='7item218':
        sculpted_feather_hilt(config)
        return
    if config['master_icon'] in ('item010','item334','item342'):
        sculpted_bone_hilt(config)
        return
    if config['master_icon']=='item009':
        obj=import_sculpted_hilt('dragon_hilt_st_v1',.38,.995)
        for name in ('gold','silver','ivory','emerald'):obj.data.materials.append(material(name))
        for poly in obj.data.polygons:
            c=poly.center;row=H-c.y/SCALE;angle=math.atan2(c.z,c.x)
            poly.material_index=0
            if row<H*.73 and abs(c.x)<H*SCALE*.034:poly.material_index=1
            elif H*.79<row<H*.93 and math.sin(angle+row/H*math.tau*14)>.25:poly.material_index=2
            elif row>H*.95:poly.material_index=3
            poly.use_smooth=True
        uv_project(obj)
        gem(CX,G,H*.015,'emerald')
        gem(CX,H*.66,H*.006,'cyan')
        return
    metal=config['metal_material'];grip=config['grip_material'];kind=config['guard']
    guard(config)
    radius=max(H*.012,min(H*.022,config['size_px'][0]*.095))
    start=G+H*.017;end=H*.94
    if kind=='double_fork':end=H*.91
    if config['master_icon'] in ('item006','7item006'):
        lathe('Leather wrapped ricasso',CX,H*.645,G,[(0,.9),(.1,1),(.9,1),(1,.9)],grip,radius*.95)
    lathe('Shaped grip',CX,start,end,[(0,.85),(.12,1),(.45,1.06),(.85,.90),(1,.83)],grip,radius)
    fitting='gold' if config['master_icon']=='7item004' else metal
    for y in (start,end):lathe('Grip collar',CX,y-H*.004,y+H*.004,[(0,.85),(.3,1),(.7,1),(1,.85)],fitting,radius*1.06)
    if kind=='artifact_collar':
        for row in (.78,.845,.90):
            lathe('Broad relic ferrule',CX,H*(row-.007),H*(row+.007),[(0,.9),(.2,1),(.8,1),(1,.9)],metal,radius*1.08)
    # Raised coarse wrapping changes silhouette; its fine grain comes from the painted maps.
    turns=8 if end-start>H*.2 else 5
    points=[]
    for i in range(turns*8+1):
        t=i/(turns*8);a=t*turns*math.tau
        points.append(point(CX+radius*1.015*math.cos(a),start+(end-start)*t,radius*1.015*SCALE*math.sin(a)))
    tube('Grip binding',points,H*SCALE*.0016,fitting if grip in ('gold','ivory','black') else grip,sides=5)
    icon=config['master_icon']
    pointed={'2hsword2','item002','item004','item005','item008','item013','item014','item333','7item002'}
    discs={'item001','item011','lsword2','7item001','7item010','cutlass1'}
    if icon in pointed:
        lathe('Faceted pointed pommel',CX,H*.943,H*.99,[(0,.65),(.18,1.45),(.43,1.45),(.92,.22),(1,.1)],metal,radius)
    elif icon in discs:
        sphere('Wheel pommel',CX,H*.962,(radius*1.7,H*.028,radius*.6),metal)
    elif kind=='artifact_collar':
        lathe('Relic pommel',CX,H*.91,H*.99,[(0,.90),(.18,1.0),(.3,.95),(.75,1.1),(.9,1.3),(1,1.3)],'silver',radius*1.25)
        for s in (-1,1):
            gem(CX+s*radius*.7,H*.957,radius*.30)
            gem(CX+s*radius*.7,H*.862,radius*.28,'cyan')
    elif kind in ('bone','serpents'):skull(CX,H*.971,radius*1.2,'bone')
    elif kind in ('d_left','d_right','shell','scroll_bow','horn_bow','ornate_bow'):
        sphere('Pommel',CX,H*.961,(radius*1.1,H*.021,radius*1.05),metal)
    else:
        sphere('Pommel',CX,H*.963,(radius*1.55,H*.027,radius*.78),metal)
    if kind in ('angular','dragon','bat','crown','artifact_collar'):
        leaf('Decorated rain guard',(CX,G-H*.012),(CX,G-H*.13),radius*.8,'rune' if kind=='angular' else metal,radius*.40)
    jewelled=kind in ('v_guard','antlers','thorns','feather','crescent','dragon','ornate_bow','double_fork','skull_arch','scroll_bow')
    if jewelled:gem(CX,G+H*.002,H*.014,'emerald' if kind=='dragon' else 'ruby')
    if kind=='angular':gem(CX,G,H*.012,'cyan')
    if config['master_icon'] in ('6brsword4','brsword3'):
        sphere('Gold blade-socket bezel',CX,G-H*.027,(H*.015,H*.014,H*.006),metal,H*SCALE*.003)
        gem(CX,G-H*.027,H*.013,'cyan')
    if config['master_icon'] in ('cutlass1','7item220'):
        gem(CX,G,H*.011)
    if kind=='scroll' and config['master_icon'] in ('2hsword3','62hsword5'):
        gem(CX,G,H*.018,'emerald')
        lathe('Gilded ricasso collar',CX,H*.56,H*.575,[(0,.65),(.5,1),(1,.7)],metal,radius)
    if config['master_icon'] in ('lsword1','lsword4','lsword5','6lsword7','2hsword1','item003','7item007','7item249','7item003'):
        colour='pinkgem' if config['master_icon']=='lsword1' else ('cyan' if config['master_icon'] in ('2hsword1','7item003') else 'ruby')
        gem(CX,H*.963,radius*1.1,colour)
    if config['master_icon']=='7item217':
        for side in (-1,1):
            vertices=[point(CX+dx,H*yy,side*z) for z in (.0029,.0035)
                      for dx,yy in ((-H*.009,.46),(H*.009,.46),(H*.009,.74),(-H*.009,.74))]
            obj=mesh('Puck — red ladder enamel inlay',vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'ladder')
            uv=obj.data.uv_layers.active.data
            for poly in obj.data.polygons:
                if abs(poly.normal.z)>.5:
                    for li in poly.loop_indices:
                        v=obj.data.vertices[obj.data.loops[li].vertex_index].co
                        uv[li].uv=(.5+v.x/(H*SCALE*.018)*.96,.02+(H*.74-(H-v.y/SCALE))/(H*.28)*.96)


def sculpted_bone_hilt(config):
    obj=import_sculpted_hilt('bone_hilt_st_v1',.30,.99)
    for name in ('silver','black','bone'):obj.data.materials.append(material(name))
    for poly in obj.data.polygons:
        c=poly.center;row=H-c.y/SCALE;angle=math.atan2(c.z,c.x)
        poly.material_index=0
        if row>H*.91:poly.material_index=2
        elif row>H*.77:poly.material_index=1 if math.sin(angle+row/H*math.tau*24)>.1 else 0
        poly.use_smooth=True
    uv_project(obj)
    gem(CX,G,H*.014)


def import_sculpted_hilt(job,fraction,bottom):
    source=PROJECT/'meshy/meshy'/job/'model_urls_glb.glb'
    previous=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o not in previous and o.type=='MESH']
    assert len(objects)==1
    obj=objects[0];obj.name=job+' — fitted sculptural hilt'
    bpy.context.view_layer.update();obj.data.transform(obj.matrix_world);obj.matrix_world=Matrix.Identity(4)
    transform=Matrix.Translation(point(CX,H*(bottom-fraction/2))) @ Matrix.Rotation(-math.pi/2,4,'X') @ Matrix.Scale(H*SCALE*fraction,4)
    obj.data.transform(transform)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    boundary=[e for e in bm.edges if e.is_boundary]
    if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),(job,'non-manifold')
    assert all(f.calc_area()>1e-12 for f in bm.faces),job
    bm.to_mesh(obj.data);bm.free();obj.data.materials.clear()
    return obj


def sculpted_feather_hilt(config):
    source=PROJECT/'meshy/meshy/iron_feather_hilt_st_v2/model_urls_glb.glb'
    previous=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o not in previous and o.type=='MESH']
    assert len(objects)==1
    obj=objects[0];obj.name='Iron Feather — sculpted wing cage and spiral hilt'
    bpy.context.view_layer.update()
    obj.data.transform(obj.matrix_world);obj.matrix_world=Matrix.Identity(4)
    length=H*SCALE*.38
    transform=Matrix.Translation(point(CX,H*.80)) @ Matrix.Rotation(-math.pi/2,4,'X') @ Matrix.Scale(length,4)
    obj.data.transform(transform)
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    boundary=[edge for edge in bm.edges if edge.is_boundary]
    if boundary:
        print('Capping Meshy socket/scan boundaries',len(boundary),flush=True)
        bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
    assert all(edge.is_manifold for edge in bm.edges),'Meshy hilt requires repair'
    assert all(face.calc_area()>1e-12 for face in bm.faces)
    bm.to_mesh(obj.data);bm.free()
    obj.data.materials.clear()
    for name in ('feather','ivory','silver'):obj.data.materials.append(material(name))
    for poly in obj.data.polygons:
        c=poly.center;row=H-c.y/SCALE
        poly.material_index=0
        if row>H*.79:
            angle=math.atan2(c.z,c.x)
            poly.material_index=1 if math.sin(angle+(row/H)*math.tau*11)>.4 else 0
        elif abs(c.x)<length*.045:poly.material_index=2
        poly.use_smooth=True
    uv_project(obj)


def pack_materials(obj,icon):
    names=[m.name for m in obj.data.materials]
    grid=2 if len(names)<=4 else 4
    size=1024;tile=size//grid;gutter=6
    images={}
    for suffix in ('base','mr','normal'):
        atlas=np.empty((size,size,4),dtype=np.float32)
        atlas[:]=(.5,.5,1,1) if suffix=='normal' else ((.5,.5,.5,1) if suffix=='base' else (1,1,1,1))
        for k,name in enumerate(names):
            src=bpy.data.images.load(str(PROJECT/'textures'/f'{name}_{suffix}.png'),check_existing=False)
            if suffix!='base':src.colorspace_settings.name='Non-Color'
            src.scale(tile-2*gutter,tile-2*gutter)
            cell=np.array(src.pixels[:],dtype=np.float32).reshape(tile-2*gutter,tile-2*gutter,4)
            padded=np.pad(cell,((gutter,gutter),(gutter,gutter),(0,0)),mode='edge')
            x=k%grid*tile;y=k//grid*tile;atlas[y:y+tile,x:x+tile]=padded
            bpy.data.images.remove(src)
        if suffix=='normal':
            assert atlas[:,:,2].min()>.75 and np.abs(atlas[:,:,:2].mean(axis=(0,1))-.5).max()<.08,'Normal atlas was colour-transformed'
        im=bpy.data.images.new(f'{icon}_{suffix}',size,size,alpha=True)
        im.colorspace_settings.name='sRGB' if suffix=='base' else 'Non-Color'
        im.pixels.foreach_set(atlas.ravel());im.filepath_raw=str(PROJECT/'textures'/f'{icon}_{suffix}.png');im.file_format='PNG';im.save()
        images[suffix]=im
    uv=obj.data.uv_layers.active.data
    for poly in obj.data.polygons:
        k=poly.material_index
        for li in poly.loop_indices:
            u,v=uv[li].uv
            uv[li].uv=((k%grid*tile+gutter+u*(tile-2*gutter))/size,(k//grid*tile+gutter+v*(tile-2*gutter))/size)
        poly.material_index=0
    mat=bpy.data.materials.new('Sword PBR — binary metal and dielectric');mat.use_nodes=True;mat.use_backface_culling=True
    tree=mat.node_tree;shader=tree.nodes.get('Principled BSDF')
    for suffix,im in images.items():
        tex=tree.nodes.new('ShaderNodeTexImage');tex.image=im
        if suffix=='base':tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
        elif suffix=='mr':
            split=tree.nodes.new('ShaderNodeSeparateColor');tree.links.new(tex.outputs['Color'],split.inputs['Color'])
            tree.links.new(split.outputs['Green'],shader.inputs['Roughness']);tree.links.new(split.outputs['Blue'],shader.inputs['Metallic'])
        else:
            normal=tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.7
            tree.links.new(tex.outputs['Color'],normal.inputs['Color']);tree.links.new(normal.outputs['Normal'],shader.inputs['Normal'])
    obj.data.materials.clear();obj.data.materials.append(mat)
    return names,tile


def finish(config):
    icon=config['master_icon'];objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bpy.context.view_layer.update()
    # The real crossguard/pommel sets the resting tilt: solve support from the actual geometry.
    for obj in objects:
        obj.data.transform(obj.matrix_world);obj.matrix_world=Matrix.Identity(4)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='SHORT_EDGE')
        bm.to_mesh(obj.data);bm.free()
        uv=obj.data.uv_layers.active.data
        area=sum(poly.area for poly in obj.data.polygons)
        uv_area=0
        for poly in obj.data.polygons:
            uvs=[uv[li].uv for li in poly.loop_indices]
            a,b,c=uvs
            uv_area+=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5
        assert area>0 and uv_area>0,obj.name
        # One physical density per material tile; the red ladder is a deliberately bespoke inlay graphic.
        if not obj.name.startswith('Puck —'):
            factor=min(1,math.sqrt(area/uv_area)/1.4)
            for loop in uv:loop.uv=(loop.uv-Vector((.5,.5)))*factor+Vector((.5,.5))
    points=[v.co.copy() for o in objects for v in o.data.vertices]
    tip=max(p.y for p in points);back=min(p.y for p in points)
    best=None
    for angle in np.linspace(-.10,.10,81):
        rotation=Matrix.Rotation(float(angle),4,'X')
        transformed=[rotation@p for p in points]
        minimum=min(p.z for p in transformed)
        tip_gap=min(p.z for p in transformed if p.y>tip-.06)-minimum
        hilt_gap=min(p.z for p in transformed if p.y<tip*.3)-minimum
        score=tip_gap+hilt_gap
        if best is None or score<best[0]:best=(score,rotation,float(angle))
    for obj in objects:obj.data.transform(best[1])
    points=[v.co for o in objects for v in o.data.vertices]
    lo=Vector(tuple(min(p[i] for p in points) for i in range(3)));hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    shift=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
    for obj in objects:
        for v in obj.data.vertices:v.co+=shift
        obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();obj=bpy.context.object;obj.name='swords_'+icon
    names,tile=pack_materials(obj,icon)
    bm=bmesh.new();bm.from_mesh(obj.data)
    assert all(e.is_manifold for e in bm.edges),icon
    assert all(f.calc_area()>1e-12 for f in bm.faces),icon
    bm.free();triangles=len(obj.data.polygons)
    assert 100<triangles<=15000,(icon,triangles)
    out=PROJECT/'work/exports'/f'swords_{icon}_export.glb'
    lod_counts=[]
    if triangles>4000:
        for level,ratio in enumerate((.5,.25,.125),1):
            lod=obj.copy();lod.data=obj.data.copy();lod.name=obj.name+f'_LOD{level}';lod.data.name=lod.name
            bpy.context.collection.objects.link(lod);bpy.context.view_layer.objects.active=lod
            modifier=lod.modifiers.new('Silhouette LOD','DECIMATE');modifier.ratio=ratio;modifier.use_collapse_triangulate=True
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            bm=bmesh.new();bm.from_mesh(lod.data)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
            assert all(e.is_manifold for e in bm.edges),(icon,level)
            assert all(f.calc_area()>1e-12 for f in bm.faces),(icon,level)
            bm.to_mesh(lod.data);bm.free();lod_counts.append(len(lod.data.polygons));lod.select_set(True)
            low=Vector(tuple(min(v.co[i] for v in lod.data.vertices) for i in range(3)))
            high=Vector(tuple(max(v.co[i] for v in lod.data.vertices) for i in range(3)))
            shift=Vector((-(low.x+high.x)/2,-(low.y+high.y)/2,-low.z))
            for vertex in lod.data.vertices:vertex.co+=shift
        bpy.context.view_layer.objects.active=obj
        (PROJECT/'work/unlinked').mkdir(exist_ok=True)
        out=PROJECT/'work/unlinked'/out.name
    bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'blends'/f'swords_{icon}.blend'))
    bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_extras=True)
    return {'triangles':triangles,'components':len(objects),'materials':names,'packed_materials':1,'texture_sizes':[1024,1024],
            'material_tile_pixels':tile-12,'support_angle_degrees':math.degrees(best[2]),'blade_ridge_thickness':.0064,
            'export':f'work/exports/swords_{icon}_export.glb','blend':f'blends/swords_{icon}.blend','lod_triangles':lod_counts}


def main():
    global SCALE,H,CX,G
    only=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set()
    designs=json.loads((PROJECT/'designs.json').read_text())
    receipt_path=PROJECT/'work/build_receipts.json';receipts=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    for key,config in designs.items():
        icon=config['master_icon']
        if only and icon not in only:continue
        bpy.ops.wm.read_factory_settings(use_empty=True);MATERIALS.clear()
        H=config['size_px'][1];SCALE=1.4/H;CX=config['grip_x'];G=config['guard_row']
        blade(config);hilt(config);receipts[icon]=finish(config)
        receipt_path.write_text(json.dumps(receipts,indent=2)+'\n')
        print('BUILT',icon,receipts[icon]['triangles'],flush=True)


if __name__=='__main__':main()
