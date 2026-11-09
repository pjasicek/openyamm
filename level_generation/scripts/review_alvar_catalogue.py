"""Build Alvar's searchable catalogue, measured comparison figures and source/render audit."""
from collections import Counter
import hashlib
import html
import json
import math
import re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from catalogue_alvar import ROOT, OUT
from catalogue_ravenshore import parse_odm_file, points

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
NOTES = {
    'Alvar poor1': 'Small pitched-roof cottage with masonry corner strips, a restrained window pattern and shallow doorstep.',
    'Alvar poor2': 'Very compact chamfered cottage, low roof and ordinary door; useful for a modest shared household.',
    'Alvar poor3': 'Longer modest cottage; add functional rear space without making the door or wall panels larger.',
    'Alvar med1': 'Simple gabled cottage with a warm tiled roof, masonry corner strips and small leaded windows.',
    'Alvar med2': 'Low hipped-roof residence. Its source medium label does not mean it is taller than every poor cottage.',
    'Alvar med3': 'Square hipped-roof house with a raised perimeter step and arched window treatment; a maintained civic/domestic option.',
    'Alvar rich1': 'Broad low articulated residence with projecting entrance bay and chimney; prominence comes from plan and trim, not height.',
    'Alvar rich2': 'Two intersecting wings with a taller roof composition. Inspect the assembled view; neither native part is an independent estate.',
    'joined four-shop block': 'One cross-shaped physical block, three BModels, four actual shop destinations. An organizational reference for joined work bays; avoid copying the symmetric whole.',
    'merchant guild civic complex': 'Three-part fortified civic complex with corner towers, parapets and a portico. Strong council/bank reference; not a ready-made tall royal castle.',
    'polygonal guild tower': 'Polygonal stone tower with a roof cap and small projecting entry; a secondary arcane silhouette, not Ellinger at its final height.',
    'temple hall': 'Broad, articulated religious hall with a conspicuous roof and dressed entrance; replace MM8 iconography for the Temple of Mok.',
    'two-part inn': 'A main guest volume and smaller entrance wing; useful for sharing a service establishment without duplicated doors.',
    'training hall': 'Broad flat-roofed hall with buttresses and a lower entrance porch; keep the detached sign separate from the occupied building.',
    'bank': 'Compact dedicated finance building; service purpose does not require a palace.',
    'stables': 'Service shelter and covered working space; a useful canopy/yard reference.',
    'landmark / infrastructure / prop': 'Reference infrastructure, prop or dungeon entrance. Do not treat it as an occupied town house.',
}
PALETTE = [('t05a01','Plain wall panel'),('t05a01c','Stone wall panel'),('t05a05','Brown roof tiles'),
           ('t05a03','Domestic timber door'),('t05b03','Dressed door'),('t05a04c','Small leaded window'),
           ('t05a04a','Arched window'),('t05c04c','Formal window panel'),('t05a07a','Masonry corner strip'),
           ('t05a10','Roof-edge / trim panel'),('t05fstep','Foundation / step'),('t05c01','Dressed civic wall')]


def people(a):
    result = []
    for h in a['houses']:
        result += [n['name'] for n in h['resident_candidates']]
        if h['proprietor']: result.append(h['proprietor']+' (proprietor)')
    return '; '.join(result) or 'No fixed house NPC/proprietor'


def dimensions(a):
    return ' × '.join(str(round(v)) for v in a['bounds']['size'])


def contact(c, title, ids):
    sheet = Image.new('RGB',(1280,math.ceil(len(ids)/4)*310+48),'#20272a'); draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT,15)
    draw.text((12,12),'Alvar — '+title+'; independently framed, dimensions are native units',font=font,fill='white')
    for j,i in enumerate(ids):
        m = c['models'][i]; a = next(a for a in c['assemblies'] if i in a['models'])
        im = Image.open(OUT/f'images/{i:03d}.png').convert('RGB'); im.thumbnail((320,260))
        x,y = j%4*320,48+j//4*310; sheet.paste(im,(x,y))
        draw.text((x+5,y+261),f'{i:03d} '+a['title'][:32],font=font,fill='white')
        draw.text((x+5,y+281),dimensions(m),font=font,fill='#dec799')
    sheet.save(OUT/f'images/contact_{title}.jpg',quality=92)


def figures(c):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle
    native = parse_odm_file(ROOT/'assets_dev/worlds/mm8/maps/out03.odm')['payload']
    colors = {'house':'#ccac85','service':'#be9257','civic':'#d3bd74','dungeon':'#94988d'}
    for town in [False,True]:
        fig,ax = plt.subplots(figsize=(13,10))
        heights = np.array(native['height_map']).reshape(128,128)*32
        ax.contour((np.arange(128)-64)*512,(64-np.arange(128))*512,heights,
                   levels=np.arange(0,8192,256),colors='#c2c9b9',linewidths=.5)
        for a in c['assemblies']:
            for i in a['models']:
                for f in native['bmodels'][i]['faces']:
                    if f['attributes']&0x2000: continue
                    ax.add_patch(Polygon(points(native['bmodels'][i],f)[:,:2],
                                         facecolor=colors.get(a['kind'],'#a8b4a5'),edgecolor='#544c41',lw=.25))
            x,y = (np.array(a['bounds']['min'])+np.array(a['bounds']['max']))[:2]/2
            if not town or (-8000<x<19500 and 9500<y<22500):
                ax.text(x,y,','.join(map(str,a['models'])),ha='center',fontsize=7,
                        bbox=dict(facecolor='white',alpha=.75,edgecolor='none',pad=1))
        ax.set(xlim=(-8000,19500) if town else (-25000,25000),ylim=(9500,22500) if town else (-25000,25000),
               aspect='equal',title='Alvar — '+('town detail' if town else 'all outdoor assemblies'),
               xlabel='Native X',ylabel='Native Y / north')
        fig.tight_layout();fig.savefig(OUT/('images/town_placement.png' if town else 'images/placement.png'),dpi=140);plt.close(fig)
    font = ImageFont.truetype(FONT,15)
    for title,entries in [('materials',[(key,key) for key in c['textures']]),('texture_roles',PALETTE)]:
        cols,tw,th = (6,220,195) if title=='materials' else (4,300,345)
        sheet=Image.new('RGB',(cols*tw,math.ceil(len(entries)/cols)*th+50),'#20272a');d=ImageDraw.Draw(sheet)
        d.text((12,12),'Alvar native materials — '+('all texture keys' if title=='materials' else 'observed architectural roles'),font=font,fill='white')
        for j,(key,role) in enumerate(entries):
            t=c['textures'][key];im=Image.open(ROOT/t['path']).convert('RGB')
            scale=min((tw-20)/im.width,(th-78)/im.height)
            im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
            x,y=j%cols*tw,50+j//cols*th;sheet.paste(im,(x+(tw-im.width)//2,y))
            d.text((x+7,y+th-65),key+' / '+'×'.join(map(str,t['size'])),font=font,fill='#dec799')
            if title!='materials':d.text((x+7,y+th-40),role,font=font,fill='white')
        sheet.save(OUT/f'images/{title}.png')
    garrote=json.loads((ROOT/'level_generation/catalogues/mm8_garrote_gorge/catalogue.json').read_text())
    selected=[('Alvar',c,[67]),('Alvar',c,[35]),('Alvar',c,[33,34]),('Alvar',c,[13,14,15]),
              ('Alvar',c,[52,53,54]),('Garrote',garrote,[31]),('Garrote',garrote,[13,14,15])]
    fig,ax=plt.subplots(figsize=(15,5));x=0
    for world,cat,ids in selected:
        a=next(a for a in cat['assemblies'] if a['models']==ids);w,_,h=a['bounds']['size']
        ax.add_patch(Rectangle((x,0),w,h,facecolor='#bba186' if world=='Alvar' else '#a1b3a0',edgecolor='#514c41'))
        ax.text(x+w/2,h+35,world+' '+','.join(map(str,ids))+'\n'+str(round(h))+' high',ha='center',fontsize=8)
        x+=w+400
    ax.axhline(176,color='#477483',ls='--',lw=1);ax.set(xlim=(-200,x),ylim=(0,1300),aspect='equal',
        title='Equal physical scale — width/height envelopes, not silhouettes',xlabel='Native width',ylabel='Height above local base')
    fig.tight_layout();fig.savefig(OUT/'images/height_profiles.png',dpi=150);plt.close(fig)
    # Same rendering method/lighting across both catalogues; labels prevent false scale comparisons.
    pairs=[('Modest home','067','031'),('Gabled home','035','024'),('Formal residence','049','041'),
           ('Civic landmark','assembly_merchant_guild','assembly_camp_keep')]
    sheet=Image.new('RGB',(1280,len(pairs)*570+50),'#20272a');d=ImageDraw.Draw(sheet)
    d.text((12,12),'Alvar (left) / Garrote Gorge (right) — style comparison; independently framed',font=font,fill='white')
    for row,(label,alvar,gg) in enumerate(pairs):
        for col,(folder,name) in enumerate([('mm8_alvar',alvar),('mm8_garrote_gorge',gg)]):
            im=Image.open(ROOT/f'level_generation/catalogues/{folder}/images/{name}.png').convert('RGB');im.thumbnail((640,520))
            x,y=col*640,50+row*570;sheet.paste(im,(x,y));d.text((x+8,y+525),label+' — '+folder+' / '+name,font=font,fill='white')
    sheet.save(OUT/'images/alvar_vs_garrote.jpg',quality=93)


def docs(c):
    assembly_by_id={a['id']:a for a in c['assemblies']}
    cards=[];lines=['# Alvar building and resident catalogue','',
        '[Searchable visual catalogue](index.html) · [House sheet](images/contact_houses.jpg) · [Service sheet](images/contact_services.jpg) · [Style comparison](images/alvar_vs_garrote.jpg) · [Castleview assessment](../../projects/mm5_castleview_kalindra/ALVAR_STYLE_COMPARISON.md) · [Measurements](catalogue.json) · [Validation](validation.json)','',
        'All 99 native Alvar BModels (`mm8/out03.odm`) are partitioned into 68 physical assemblies. There are 47 distinct active house destinations, 35 initial NPC-table occupants and 12 named service proprietors. The 34 residential assemblies each have one initial NPC; the merchant guild adds Bastian Loudrin. These populations are reported separately, without simulating quest-state dialogue.','',
        '## Assemblies, residents and services','',
        '| Assembly | Parts | Dimensions XYZ | Residents / proprietor | Active destinations |',
        '| --- | --- | --- | --- | --- |']
    for a in c['assemblies']:
        destinations='; '.join(f'{h["id"]}: {h["name"]}' for h in a['houses']) or ', '.join(a['destinations']) or '—'
        lines.append(f'| {a["title"]} | {a["models"]} | {dimensions(a)} | {people(a)} | {destinations} |')
    lines+=['','## Script destinations without an active outdoor BModel entrance','',
        'These are accounted for but excluded from the physical-house census. A Lua registration alone does not establish a building location. This review does not infer a nearby house or assert that every unbound event is unreachable through all other mechanisms.','',
        '| House | Events | Initial occupants |','| --- | --- | --- |']
    for r in c['unbound_script_houses']:
        h=r['house'];lines.append(f'| {h["id"]}: {h["name"]} | {r["events"]} | '+', '.join(n['name'] for n in h['resident_candidates'])+' |')
    lines+=['','## Measurements and interpretation','',
        '- The four-shop block is parts 13–15, with four different destinations. It is neither three houses nor four independent meshes.',
        '- Estate pairs 33–34,38–39,45–46,56–57 are one household each. Merchant Guildhouse 52–54, fountain 79–80 and inns 95–96/97–98 are likewise assembled before counting.',
        '- Detached training sign 94 is a hint-only prop. It does not add another training venue or occupant.',
        '- Exact face bounds, normals, UV offsets, texture dimensions and units per texel are in JSON. Door samples include all visible vertical event faces; a full clickable facade is not automatically a door-sized opening.',
        '- Three empty-texture waterfall faces are invisible native geometry and are excluded from the texture palette; visible missing materials are rejected.',
        '- The current merged registry gives Guild Training Hall house 1566. Original aliases and current global IDs are not interchangeable.',
        '- Every material image uses unchanged local native texture art. MM5 models will be independently authored; this is a reference catalogue.',
        '', '## Rebuild','',
        '1. Run `python3 level_generation/scripts/catalogue_alvar.py`.',
        '2. Execute `blender_building_catalogue.py` through Blender MCP with `CATALOGUE="mm8_alvar"`, batches of `MODEL_IDS`, and the `ASSEMBLIES` ids listed in `catalogue.json`. The renderer creates a separate study scene and restores the active scene after each batch.',
        '3. Run `python3 level_generation/scripts/review_alvar_catalogue.py` after all 99 part views and 22 assembly/context views exist.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    for m in c['models']:
        a=assembly_by_id[m['assembly']];note=NOTES[m['family']]
        text=[f'# {m["index"]:03d}: {m["name"]}','',f'![Native reference](../images/{m["index"]:03d}.png)','',
            f'Assembly: **{a["title"]}**; parts {a["models"]}.',f'Dimensions XYZ: {dimensions(m)} native units.',
            '',note,'','## Residents and services','',f'Actual assembly occupancy: {people(a)}.']
        for h in a['houses']:
            text.append(f'- House {h["id"]}: {h["name"]}; type {h["type"]}; proprietor {h["proprietor"] or "none"}.')
            for n in h['resident_candidates']:
                text.append('  - '+n['name']+' — '+'; '.join(t['title'] for t in n['topics']))
        if a['destinations']:text.append('Map destinations: '+', '.join(a['destinations']))
        text += ['','## Entrance bindings','',*['- Event '+str(s['event'])+': active faces '+str(s['active_faces'])+'; label-only faces '+str(s['label_only_faces']) for s in m['services']],
                 '', '## Materials','',*['- '+(key or '(invisible/untextured)')+f': {count} faces' for key,count in m['materials'].items()]]
        (OUT/f'models/{m["index"]:03d}.md').write_text('\n'.join(text)+'\n')
        search=html.escape((m['name']+' '+m['family']+' '+a['title']+' '+people(a)+' '+json.dumps(a['houses'])+' '+json.dumps(m['materials'])).lower(),quote=True)
        cards.append(f'<article data-search="{search}"><a href="models/{m["index"]:03d}.md"><img loading="lazy" src="images/{m["index"]:03d}.png"></a><h3>{m["index"]:03d} {html.escape(a["title"])}</h3><p>{html.escape(people(a))}</p><p>{html.escape(note)}</p><small>{dimensions(m)} native units</small></article>')
    views=''.join(f'<article><img loading="lazy" src="images/assembly_{a["id"]}.png"><h3>{html.escape(a["purpose"])}</h3><p>Parts {a["models"]}</p></article>' for a in c['assembly_views'])
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Alvar architecture catalogue</title><style>body{background:#20272a;color:#e1e5db;font:15px system-ui;margin:25px}a{color:#b8d5de}p{line-height:1.5}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}article{padding:12px;background:#30393b;border:1px solid #56605c}article img{width:100%}.wide{width:100%;max-width:1400px}input{font:inherit;padding:10px;width:min(700px,95%)}small{color:#dec799}</style><h1>Alvar: buildings, residents and civic architecture</h1><p>99 native parts · 68 assemblies · 47 active house destinations · 35 initial NPCs + 12 service proprietors. Original geometry is used only for reference.</p><p><a href="README.md">Complete inventory and unbound events</a> · <a href="catalogue.json">Face / UV / entrance measurements</a> · <a href="validation.json">Validation</a> · <a href="../../projects/mm5_castleview_kalindra/ALVAR_STYLE_COMPARISON.md">Castleview recommendation</a> · <a href="../mm8_garrote_gorge/index.html">Garrote catalogue</a> · <a href="../mm8_ravenshore/index.html">Ravenshore catalogue</a></p><h2>Alvar versus Garrote</h2><p>These views compare construction and material character. Each image is independently framed; use the measured dimensions below for scale.</p><img class="wide" src="images/alvar_vs_garrote.jpg"><img class="wide" src="images/height_profiles.png"><h2>Original map placement</h2><img class="wide" src="images/town_placement.png"><details><summary>Whole Alvar region</summary><img class="wide" src="images/placement.png"></details><h2>Material roles</h2><img class="wide" src="images/texture_roles.png"><details><summary>All 89 native materials</summary><img class="wide" src="images/materials.png"></details><p><a href="images/contact_houses.jpg">All house parts</a> · <a href="images/contact_services.jpg">Services / civic parts</a> · <a href="images/contact_other.jpg">Other structures</a></p><h2>Assembled structures and town groups</h2><section>VIEWS</section><h2>Every part, residents and material family</h2><input id="search" placeholder="Search resident, service, house family or texture…"><section id="parts">CARDS</section><script>document.querySelector('#search').oninput=e=>document.querySelectorAll('#parts article').forEach(a=>a.style.display=a.dataset.search.includes(e.target.value.toLowerCase())?'':'none');</script></html>'''
    (OUT/'index.html').write_text(page.replace('VIEWS',views).replace('CARDS',''.join(cards)))


def validate(c):
    assert sorted(i for a in c['assemblies'] for i in a['models'])==list(range(99))
    expected=[(f'{m["index"]:03d}',[m['index']]) for m in c['models']]
    expected += [('assembly_'+a['id'],a['models']) for a in c['assembly_views']]
    for name,ids in expected:
        r=json.loads((OUT/f'images/{name}.json').read_text());assert r['models']==ids
        with Image.open(OUT/f'images/{name}.png') as im:assert im.size==(800,650);im.verify()
    for s in c['sources']+list(c['textures'].values()):assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256'],s['path']
    houses={h['id']:h for a in c['assemblies'] for h in a['houses']}
    assert len(houses)==47 and sum(len(h['resident_candidates']) for h in houses.values())==35
    assert sum(bool(h['proprietor']) for h in houses.values())==12
    residential=[a for a in c['assemblies'] if a['kind']=='house']
    assert len(residential)==34 and all(a['npcCount']==1 for a in residential)
    assert {(f['width'],f['height']) for a in residential for f in a['entrance_faces']}=={(128.0,256.0)}
    assert len({i for a in c['assemblies'] for h in a['houses'] for i in [h['id']]})==sum(len(a['houses']) for a in c['assemblies'])
    for m in c['models']:
        assert len(m['face_records'])==m['faces']
        for s in m['services']:
            assert all(m['face_records'][i]['event']==s['event'] for i in s['active_faces'])
    result=dict(passed=True,parts=99,physicalAssemblies=len(c['assemblies']),renderedViews=len(expected),
        houses=47,npcRows=35,serviceProprietors=12,textures=len(c['textures']),unboundScriptHouses=10,
        limitations=c['limits'])
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


def build():
    c=json.loads((OUT/'catalogue.json').read_text())
    for name,kinds in [('houses',{'house'}),('services',{'service','civic'}),('other',{'dungeon','bridge','prop','landscape','camp'})]:
        ids=[i for a in c['assemblies'] if a['kind'] in kinds for i in a['models']]
        contact(c,name,ids)
    figures(c);docs(c);validate(c)

if __name__=='__main__':build()
