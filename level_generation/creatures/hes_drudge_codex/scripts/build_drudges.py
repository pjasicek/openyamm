#!/usr/bin/env python3
"""Drudge caste authoring from the immutable shared body. Coordinates are glTF (+Y up, +Z front).
Runtime tiers use shared textures and ramps. Only Thrix's distinct healed-scar pattern is baked.
Rigid additions are exported in their attachment bone's local frame, with matching viewer geometry.
"""
import copy, hashlib, json, sys, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
ROOT = Path(__file__).resolve().parents[3]
PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT.parent / 'tools'), str(ROOT / 'creatures/claude_shared/floor'), str(ROOT / 'creatures/claude_shared')]
from glb_pose import Glb, Model
from merge_head_material import append_accessor, add_image, image_of, write_glb, compact
import kreegan_skin
SOURCE = ROOT / 'creatures/hes_kreegan_claude/export/hes_kreegan.glb'
SOURCE_HASH = '38cc3345adbebe78ee535f2430886ee52899270951767a938ede58094eafbc11'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH, 'Shared body changed: inspect before rebuilding'
LUMA = np.array([.2126, .7152, .0722])
def linear(c): return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
def srgb(c): return np.where(c <= .0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1/2.4) - .055)
def ramp(colors, t):
    colors = np.asarray(colors); x = np.clip(t, 0, 1) * (len(colors)-1)
    i = np.minimum(x.astype(int), len(colors)-2); f = (x-i)[...,None]
    return colors[i]*(1-f) + colors[i+1]*f

def baked(doc, binary, mat):
    image, _ = image_of(doc, binary, mat['pbrMetallicRoughness']['baseColorTexture']['index'])
    color = linear(np.asarray(image.convert('RGB'), float)/255)
    mask, _ = image_of(doc, binary, mat['extras']['openyamm_region_mask']['index'])
    mask = np.asarray(mask.convert('RGB').resize(image.size, Image.Resampling.BILINEAR),float)/255
    lum = color @ LUMA; out = color.copy()
    for c, r in enumerate(mat['extras']['openyamm_region_ramps']):
        lo,hi = r['range']; w = mask[...,c:c+1]
        out = out*(1-w) + ramp(r['colors'],(lum-lo)/(hi-lo))*w
    return Image.fromarray(np.uint8(np.clip(srgb(out),0,1)*255+.5))

def scars(glb, image):
    # Rasterize LOD0 skin positions into its existing atlas; scars follow the skin, including across UV seams.
    im = np.asarray(image).copy(); h,w = im.shape[:2]
    mesh = glb.json['meshes'][0]
    for prim in mesh['primitives']:
        if not glb.json['materials'][prim['material']]['name'].startswith('HSD'): continue
        p = glb.accessor(prim['attributes']['POSITION']); uv = glb.accessor(prim['attributes']['TEXCOORD_0'])
        for tri in glb.accessor(prim['indices']).astype(int).reshape(-1,3):
            xyz = p[tri]
            if xyz[:,1].max()<1.22 or xyz[:,1].min()>1.49 or xyz[:,2].max()<.27: continue
            q = uv[tri]*[w,h]; lo=np.maximum(np.floor(q.min(0)).astype(int),0); hi=np.minimum(np.ceil(q.max(0)).astype(int),[w-1,h-1])
            if (lo>hi).any(): continue
            x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
            den=(q[1,0]-q[0,0])*(q[2,1]-q[0,1])-(q[1,1]-q[0,1])*(q[2,0]-q[0,0])
            if abs(den)<1e-8: continue
            b=((x-q[0,0])*(q[2,1]-q[0,1])-(y-q[0,1])*(q[2,0]-q[0,0]))/den
            c=((q[1,0]-q[0,0])*(y-q[0,1])-(q[1,1]-q[0,1])*(x-q[0,0]))/den
            a=1-b-c; pos=a[...,None]*xyz[0]+b[...,None]*xyz[1]+c[...,None]*xyz[2]
            weight=np.zeros_like(a)
            for cx,cy,rx,ry in [(.22,1.395,.036,.018),(.29,1.35,.028,.022),(.10,1.34,.024,.017),(-.07,1.295,.026,.012)]:
                r=np.sqrt(((pos[...,0]-cx)/rx)**2+((pos[...,1]-cy)/ry)**2)
                ring=np.exp(-((r-1)/.20)**2)*.85
                weight=np.maximum(weight,ring)
            weight*=((a>=0)&(b>=0)&(c>=0)&(pos[...,2]>.28))
            tile=im[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
            tile[:]=np.uint8(tile*(1-weight[...,None])+np.array([172,153,161])*weight[...,None])
    return Image.fromarray(im)

def body():
    g=Glb(SOURCE); d=g.json
    d['asset']['generator']='OpenYAMM Drudge caste; shared body preserved'
    for v in d['extensions']['KHR_materials_variants']['variants']: v['name']=v['name'].replace('hkr_','hsd_')
    # Every Drudge tier takes the luminance spread of the Trooper A skin ramp (no lifted highlights in it).
    spread=next(m for m in d['materials'] if m['name']=='HKR_A')['extras']['openyamm_region_ramps'][0]
    for m in d['materials']:
        if m['name'].startswith('HKR'):
            m['name']=m['name'].replace('HKR','HSD')
            # Drudge skins (clay, ash grey, rust; kreegan_skin.py) on the body's own skin range; harness 15 % darker.
            r=m['extras']['openyamm_region_ramps']; tier=m['name'].split('_')[1].lower()
            r[0]=kreegan_skin.recolour({'range':r[0]['range'],'colors':spread['colors']},kreegan_skin.SKIN['drudge'][tier])
            r[1]['colors']=(np.asarray(r[0]['colors'])*.85).round(6).tolist()
        if m['name']=='Demon_Iris':
            m['emissiveFactor']=[.045,.20,.42]; m['pbrMetallicRoughness']['baseColorFactor']=[.09,.36,.65,1]
    # The mandated export already has far baked atlases. Rebuild from its final LOD0, retaining LOD1.
    byname={m['name']:i for i,m in enumerate(d['materials'])}
    for mesh in d['meshes']:
        for prim in mesh['primitives']:
            if 'material' in prim:
                prim['material']=byname[re.sub(r'_LOD[23]$', '', d['materials'][prim['material']]['name'])]
            for mapping in prim.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):
                mapping['material']=byname[re.sub(r'_LOD[23]$', '', d['materials'][mapping['material']]['name'])]
    g.json,g.bin=compact(d,g.bin);d=g.json
    write_glb(PROJECT/'work/drudge_before_lod.glb',d,g.bin)
    (PROJECT/'textures/drudge_ramps.json').write_text(json.dumps({m['name']:m['extras']['openyamm_region_ramps'] for m in d['materials'] if m['name'].startswith('HSD')},indent=1)+'\n')
    thrix=Glb(PROJECT/'work/drudge_before_lod.glb'); td=thrix.json
    td.pop('extensions',None); td['extensionsUsed']=[x for x in td.get('extensionsUsed',[]) if x!='KHR_materials_variants']
    # Distinct character pattern; no runtime tint or variant on Thrix. His own pale grey-pink skin (kreegan_skin.py)
    # is baked; the harness stays 15 % darker than the skin.
    for mesh in td['meshes']:
        for p in mesh['primitives']: p.pop('extensions',None)
    for m in td['materials']:
        if not m['name'].startswith('HSD'): continue
        r=m['extras']['openyamm_region_ramps']
        r[0]=kreegan_skin.recolour(r[0],kreegan_skin.BOSS['thrix'])
        r[1]['colors']=(np.asarray(r[0]['colors'])*.85).tolist()
        img=baked(td,thrix.bin,m)
        if m['name']=='HSD_A':
            img=scars(thrix,img); img.save(PROJECT/'textures/thrix_scar_basecolor.png')
        ti=add_image(td,thrix.bin,img,'Thrix_healed_'+m['name'],0)
        m['pbrMetallicRoughness']['baseColorTexture']={'index':ti}
        m['extras'].pop('openyamm_region_ramps'); m['extras'].pop('openyamm_region_mask')
        m['name']='Thrix_'+m['name']
    thrix.json,thrix.bin=compact(td,thrix.bin)
    write_glb(PROJECT/'work/thrix_before_lod.glb',thrix.json,thrix.bin)
    return g

def material(name,color,metal=0,rough=.8,emit=None):
    m={'name':name,'pbrMetallicRoughness':{'baseColorFactor':[*linear(np.array(color)/255),1.0], 'metallicFactor':metal,'roughnessFactor':rough}}
    if emit: m['emissiveFactor']=emit
    return m

class Part:
    def __init__(self,name,joint,model):
        self.name,self.joint=name,joint
        self.inverse=np.linalg.inv(model.world({})[[n.get('name') for n in model.glb.json['nodes']].index(joint)])
        self.vertices=[];self.faces=[];self.mats=[]
    def slab(self,outline,thickness,mat,bevel=.008):
        # Convex chipped outline ordered CCW as seen from outside (+Z); bevel supplies readable broken edges.
        p=np.array(outline,float); centre=p.mean(0); n=len(p); start=len(self.vertices)
        inside=centre+(p-centre)*.90; inside[:,2]+=bevel
        back=p.copy();back[:,2]-=thickness
        vertices=np.concatenate([p,inside,back,[inside.mean(0)],[back.mean(0)]])
        self.vertices.extend(vertices.tolist())
        for i in range(n):
            j=(i+1)%n
            for f in [(n+i,n+j,3*n),(i,j,n+j),(i,n+j,n+i),(i,2*n+i,2*n+j),(i,2*n+j,j),(2*n+j,2*n+i,3*n+1)]:
                self.faces.append([start+k for k in f]);self.mats.append(mat)
    def export(self,materials):
        p=np.array(self.vertices);p=(self.inverse@np.c_[p,np.ones(len(p))].T).T[:,:3]
        d={'asset':{'version':'2.0','generator':'OpenYAMM Drudge hand-authored attachment'},'scene':0,'scenes':[{'nodes':[0]}],
           'nodes':[{'name':self.name,'mesh':0}], 'meshes':[{'name':self.name,'primitives':[]}], 'buffers':[{'byteLength':0}],
           'bufferViews':[],'accessors':[],'materials':copy.deepcopy(materials),'textures':[],'images':[]}
        binary=bytearray();tri=np.array(self.faces); groups=np.array(self.mats)
        # One neutral wear set for the original rigid additions; authored base factors describe each material.
        rng=np.random.default_rng(281); h=w=256
        grain=rng.normal(0,3,(h,w)); broad=np.asarray(Image.fromarray(np.uint8(rng.uniform(90,210,(16,16)))).resize((w,h),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(4)),float)
        value=np.clip(211+grain+(broad-150)*.22,160,245)
        paint=Image.fromarray(np.uint8(np.repeat(value[...,None],3,axis=2)))
        draw=ImageDraw.Draw(paint)
        for k in range(12):
            x,y=rng.integers(0,256,2);draw.line([(int(x),int(y)),(int(x+7),int(y+12)),(int(x+4),int(y+22))],fill=(151,148,141),width=1)
        dx,dy=np.gradient(value/255)
        normal=np.dstack([-dy*.8,-dx*.8,np.ones_like(value)]);normal/=np.linalg.norm(normal,axis=2)[...,None]
        maps={'wear_basecolor':paint,'wear_normal':Image.fromarray(np.uint8((normal*.5+.5)*255)),
              'wear_orm':Image.fromarray(np.uint8(np.dstack([np.full_like(value,30),np.clip(218+(broad-150)*.2,190,240),np.full_like(value,255)])))}
        tex={}
        for name,img in maps.items():
            img.save(PROJECT/'textures'/(name+'.png'));tex[name]=add_image(d,binary,img,name,None)
        for material_ in d['materials']:
            material_['pbrMetallicRoughness']['baseColorTexture']={'index':tex['wear_basecolor']}
            material_['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':tex['wear_orm']}
            material_['normalTexture']={'index':tex['wear_normal'],'scale':.4}
        # Separate face corners: hard fractured edges coincide with UV seams; no sliver tessellation.
        for mi in sorted(set(self.mats)):
            t=tri[groups==mi];v=p[t].reshape(-1,3)
            normal=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]])
            normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
            assert np.isfinite(normal).all()
            a={}
            for key,val in [('POSITION',v),('NORMAL',np.repeat(normal,3,axis=0))]:
                a[key]=append_accessor(d,binary,np.float32(val),{'componentType':5126,'type':'VEC3'},34962)
            uv=[]
            for face, norm in zip(p[t],normal):
                axes=[i for i in range(3) if i!=np.argmax(np.abs(norm))]
                uv.extend((face[:,axes]*4).tolist())
            a['TEXCOORD_0']=append_accessor(d,binary,np.float32(uv),{'componentType':5126,'type':'VEC2'},34962)
            index=append_accessor(d,binary,np.arange(len(v),dtype=np.uint16),{'componentType':5123,'type':'SCALAR'},34963)
            d['meshes'][0]['primitives'].append({'attributes':a,'indices':index,'material':mi})
        out=PROJECT/'export'/f'hes_drudge_{self.name}.glb';write_glb(out,d,binary)
        return {'file':out.name,'node':self.joint,'triangles':len(tri),'world_bounds':[np.min(self.vertices,0).tolist(),np.max(self.vertices,0).tolist()]}

def attachments(model):
    mats=[material('Fractured_ivory',(171,158,128)),material('Broken_ceramic_edge',(99,92,78)),
          material('Ancient_gold_remnant',(144,105,42),.65,.6),material('Dark_resin',(40,30,36),0,.88),
          material('Dim_orange_join',(97,43,17),0,.8,[.28,.065,.009]),material('Torn_umber_scarf',(89,78,72),0,.95),
          material('Scarf_fold',(65,55,52),0,1)]
    shoulder=Part('shoulder','B_L_Pauldron',model)
    # A single salvaged plate, angled over the outside of the left shoulder, with a chipped lower corner.
    shoulder.slab([(.18,1.30,.377),(.35,1.29,.333),(.39,1.38,.278),(.34,1.48,.242),(.23,1.49,.262),(.16,1.41,.325)],.028,0)
    shoulder.slab([(.21,1.42,.334),(.34,1.405,.300),(.335,1.425,.291),(.22,1.44,.323)],.004,2,.001)
    shoulder.slab([(.19,1.30,.362),(.32,1.30,.329),(.31,1.32,.334),(.20,1.32,.365)],.02,3,.001)
    chest=Part('slabs','B_Spine2',model)
    chest.slab([(-.115,1.235,.432),(.07,1.245,.431),(.115,1.31,.436),(.08,1.405,.432),(-.105,1.40,.425),(-.13,1.335,.431)],.028,0)
    chest.slab([(-.09,1.385,.444),(.065,1.391,.451),(.065,1.403,.449),(-.095,1.398,.444)],.004,2,.001)
    chest.slab([(.075,1.26,.434),(.12,1.28,.425),(.135,1.33,.421),(.115,1.34,.436)],.016,3,.003)
    chest.slab([(.116,1.285,.438),(.127,1.29,.434),(.133,1.32,.432),(.122,1.325,.441)],.004,4,.001)
    scarf=Part('scarf','B_Spine2',model)
    # Short folded strip below the jaw; asymmetric torn end leaves the healed graft sites exposed.
    scarf.slab([(-.11,1.415,.414),(.10,1.423,.412),(.10,1.461,.396),(-.10,1.46,.397)],.012,5,.005)
    scarf.slab([(-.105,1.418,.425),(.08,1.432,.425),(.09,1.444,.418),(-.10,1.436,.425)],.004,6,.001)
    scarf.slab([(-.10,1.256,.439),(-.055,1.29,.441),(-.043,1.277,.443),(-.020,1.32,.440),(-.044,1.425,.436),(-.113,1.42,.432)],.009,5,.004)
    return [x.export(mats) for x in [shoulder,chest,scarf]]

if __name__=='__main__':
    g=body(); parts=attachments(Model(g))
    (PROJECT/'export/attachments.json').write_text(json.dumps(parts,indent=2)+'\n')
    print(json.dumps(parts,indent=2))
