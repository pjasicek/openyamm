"""Native Garrote Gorge building, occupant, wall and material reference catalogue.

Original geometry is inspected/rendered only in a reference scene; it is not imported into MM5 content.
"""
from collections import Counter,defaultdict
import csv
import html
import json
from pathlib import Path
import re
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import yaml
from catalogue_ravenshore import ROOT,events,table,source,points,bounds,face_measure,parse_odm_file

OUT=ROOT/'level_generation/catalogues/mm8_garrote_gorge'
# Partition all 56 BModels by physical assembly, independently of duplicated hint labels.
GROUPS=[('dragon_cave',[0,1],'Dragon Cave entrance','dungeon'),('chest_east_1',[2],'Eastern chest 1','prop'),
 ('chest_east_2',[3],'Eastern chest 2','prop'),('eep',[4],'Grand Temple of Eep entrance','dungeon'),
 ('obelisk',[5],'Obelisk','prop'),('tents_a',[6],'Training tents A','camp'),('tents_b',[7],'Training tent B','camp'),
 ('tents_c',[8],'Training tents C','camp'),('camp_walls',[9,10,11,12],'Dragon Hunter Camp walls and gate','walls'),
 ('camp_keep',[13,14,15],'Dragon Hunter Camp keep','keep'),('magic',[16],'Wards and Pendants','service'),
 ('temple',[17],'Sacred Steel','service'),('stables',[18],'Guild Caravans','service'),('weapon',[19],"Lance’s Spears",'service'),
 ('armor',[20],'Plated Protection','service'),('inn',[21,22],"Dragon’s Blood Inn",'service'),
 ('well_camp',[23],'Camp well','prop'),('ironfist',[24],'Ironfist Residence','house'),
 ('foestryke',[25],'Foestryke Residence','house'),('well_village_a',[26],'Village well A','prop'),
 ('calandril',[27],"Calandril’s Residence",'house'),('maker',[28],'Maker Residence','house'),
 ('kern',[29],'Kern Residence','house'),('well_village_b',[30],'Village well B','prop'),
 ('morningstar',[31],'Morningstar Residence','house'),('reaverston',[32],'Reaverston Residence','house'),
 ('bridge',[33,34],'River bridge','bridge'),('otterton',[35,36],'Otterton Residence','house'),
 ('arin',[37,38],'Arin Residence','house'),('weldrick',[39,40],"Weldrick’s Home",'house'),
 ('slayer',[41],'Slayer Residence','house'),('nelix',[42],"Nelix’s House",'house'),
 ('jeni',[43],'Jeni Residence','house'),('tempus',[44],"Tempus’ House",'house'),
 ('avalon',[45],"Avalon’s Residence",'house'),('stormlance',[46],'Stormlance Residence','house'),
 ('lightsworn',[47],'Lightsworn Residence','house'),('chest_south',[48],'Southern chest','prop'),
 ('naga_vault',[49,50,51,52,53],'Naga Vault entrance complex','dungeon'),
 ('training',[54,55],"Godric’s Gauntlet",'service')]


def family(i,name):
    if 9<=i<=12:return 'camp curtain / gate'
    if 13<=i<=15:return 'camp keep'
    if 16<=i<=22 or i>=54:return 'special service building'
    if '_poor2' in name:return 'small masonry cottage'
    if '_poor1' in name:return 'long masonry cottage'
    if '_med1' in name:return 'tall narrow house'
    if '_med2' in name:return 'compact middle house'
    if 'rich2' in name:return 'joined wing residence'
    if 'rich1' in name:return 'compact dressed residence'
    return next(g[3] for g in GROUPS if i in g[1])


def build():
    for child in ['models','images']: (OUT/child).mkdir(parents=True,exist_ok=True)
    base=ROOT/'assets_dev/worlds/mm8';mp=base/'maps/out05.odm';sp=base/'maps/out05.scene.yml';lp=base/'events/maps/out05.lua'
    native=parse_odm_file(mp)['payload'];sc=yaml.safe_load(sp.read_text());ev=events(lp)
    hs,npcs,topics=table('house_data.txt'),table('npc.txt'),table('npc_topic.txt')
    paths={}
    for root in [base,ROOT/'assets_dev/engine']:
        for category in ['textures','terrain']:
            for path in sorted((root/category).glob('*.bmp')):paths.setdefault(path.stem.lower(),path)
    for o in sc.get('bmodel_faces',{}).get('interactive_faces',[]):
        f=native['bmodels'][o['bmodel_index']]['faces'][o['face_index']]
        for k in ['cog_number','cog_triggered_number','cog_trigger']:f[k]=o[k]
        f['attributes']=o['legacy_attributes']
    assert not sc.get('initial_state',{}).get('face_attribute_overrides'), 'Inspect dynamic initial face changes explicitly'
    def house(h):
        r=hs[h]['row'];res=[]
        for ni,nn in npcs.items():
            nr=nn['row']
            if len(nr)>15 and nr[6].isdigit() and int(nr[6])==h:
                res.append(dict(id=ni,name=nr[1].strip(),line=nn['line'],portrait=nr[2],
                  topics=[dict(id=int(v),title=topics.get(int(v),{}).get('row',['',''])[1]) for v in nr[10:16] if v.isdigit() and int(v)]))
        return dict(id=h,name=r[5],type=r[2],proprietor=r[6] if r[6]!='Placeholder' else None,proprietor_title=r[7],resident_candidates=res,line=hs[h]['line'])
    records=[];used=set()
    for i,m in enumerate(native['bmodels']):
        faces=[face_measure(m,f,paths) for f in m['faces']];used.update(f['texture'].lower() for f in faces)
        direct=defaultdict(list);labels=defaultdict(list)
        for f in faces:
            e=ev.get(f['event'],{})
            if e.get('houses') or e.get('destinations'):direct[e['id']].append(f['index'])
            elif e.get('label_for_event'):labels[e['label_for_event']].append(f['index'])
        services=[]
        for number in sorted(set(direct)|set(labels)):
            e=ev[number];services.append(dict(event=number,title=e['title'],active_faces=direct[number],
                label_only_faces=labels[number],houses=[house(h) for h in e['houses']],destinations=e['destinations'],line=e['line']))
        records.append(dict(index=i,name=m['name'],family=family(i,m['name']),bounds=bounds(points(m)),
            vertices=len(m['vertices']),faces=len(faces),materials=dict(Counter(f['texture'] for f in faces)),face_records=faces,
            services=services,has_active_entry=bool(direct),catalogue_building=True,
            assembly=next(g[0] for g in GROUPS if i in g[1]),
            hint_events=[dict(id=j,title=ev[j]['title']) for j in sorted({f['event'] for f in faces}) if j in ev and ev[j]['title']]))
    assemblies=[]
    for gid,ids,title,kind in GROUPS:
        allpoints=np.concatenate([points(native['bmodels'][i]) for i in ids]);active_houses={}
        destinations=set();doors=[]
        for i in ids:
            for s in records[i]['services']:
                if s['active_faces']:
                    destinations.update(s['destinations']);active_houses.update({h['id']:h for h in s['houses']})
                    for fi in s['active_faces']:
                        f=records[i]['face_records'][fi]
                        if not f['invisible'] and abs(f['normal'][2])<.5:
                            size=f['bounds']['size'];doors.append(dict(model=i,face=fi,texture=f['texture'],
                                event=s['event'],width=round(float(np.hypot(size[0],size[1])),2),height=size[2],
                                texture_dimensions=f['texture_dimensions'],units_per_texel=f['edge_units_per_texel_median']))
        interiors=[]
        for dest in sorted(destinations):
            p=base/f'events/maps/{Path(dest).stem}.lua'
            if p.exists():
                for h in sorted({h for e in events(p).values() for h in e['houses']}):interiors.append(house(h))
        assemblies.append(dict(id=gid,models=ids,title=title,purpose=title,kind=kind,bounds=bounds(allpoints),
            houses=list(active_houses.values()),destinations=sorted(destinations),interior_houses=interiors,
            entrance_faces=doors,npcCount=sum(len(h['resident_candidates']) for h in active_houses.values()),
            note='Part039 carries Otterton’s stale hint label, but physically joins040 and the actual entrance is Weldrick house571. The label does not move Otterton’s resident here.' if gid=='weldrick' else
                 'Multiple BModels form one physical assembly; count residents by unique actual house destination.' if len(ids)>1 else 'One native part; occupants are initial table candidates.'))
    textures={k:dict(source(paths[k]),size=list(Image.open(paths[k]).size)) for k in sorted(used) if k in paths}
    assert used<=paths.keys(), sorted(used-paths.keys())
    sources=[mp,sp,lp,base/'events/maps/out05_mmmerge.lua']+[ROOT/'assets_dev/engine/data_tables'/f for f in ['house_data.txt','npc.txt','npc_topic.txt']]
    sources += [base/f'events/maps/{d}.lua' for d in ['d16','d17','d18','d44']]
    cat=dict(format_version=1,title='Garrote Gorge',map='mm8/out05.odm',study_scene='Garrote Gorge building catalogue',
      object_prefix='GarroteCatalogue',models=records,assemblies=assemblies,
      assembly_views=[dict(id=a['id'],models=a['models'],purpose=a['title']) for a in assemblies if len(a['models'])>1]+
         [dict(id='camp_complete',models=list(range(9,24)),purpose='Full walled camp with keep and six service buildings'),
          dict(id='village_complete',models=list(range(24,33))+list(range(35,48)),purpose='Village houses at original spacing')],
      textures=textures,sources=[source(p) for p in sources if p.exists()],
      coverage=dict(all_bmodels=len(records),physical_assemblies=len(assemblies),house_destinations=len({h['id'] for a in assemblies for h in a['houses']}),
          npc_rows=sum(a['npcCount'] for a in assemblies),house_assemblies=sum(a['kind']=='house' for a in assemblies),service_assemblies=sum(a['kind']=='service' for a in assemblies)),
      limits=['Read-only catalogue of original BModels; none are transplanted into MM5 geometry.',
              'Initial merged-base NPC assignments and house-table proprietors are different populations; no quest-state simulation.',
              'Door samples include all visible vertical event faces; inspect textures and dimensions before treating a whole event facade as a door.',
              'Names rich/med/poor are asset families, not proven NPC wealth; resident count does not dictate footprint.',
              'Part039 label mismatch is recorded rather than propagated into assembly occupancy.',
              'Neutral independently fitted views cannot establish relative physical scale; use the numeric dimensions / equal-scale figures.'])
    (OUT/'catalogue.json').write_text(json.dumps(cat,indent=2)+'\n')
    (OUT/'textures.json').write_text(json.dumps(textures,indent=2)+'\n')
    write_docs(cat);figures(cat,native)
    print(json.dumps(cat['coverage']))
    print('Material families',Counter(k[:3] for k in textures))


def write_docs(c):
    lines=['# Garrote Gorge building and resident catalogue','',
       '[Searchable visual catalogue](index.html) · [House contact sheet](images/contact_houses.jpg) · [Walls/keep sheet](images/contact_walls_keep.jpg) · [Material roles](images/texture_roles.png) · [Complete face/UV/occupancy data](catalogue.json) · [MM5 mapping](../../projects/mm5_castleview_kalindra/GARROTE_STYLE_MAPPING.md)','',
       'All 56 native BModels are inventoried and partitioned into physical assemblies. Original geometry is used only for reference views; new MM5 geometry must be authored independently.',
       '', '## Assemblies and occupants','',
       '| Assembly | BModels | Dimensions XYZ | Occupants / proprietor | Actual house destinations |','| --- | --- | --- | --- | --- |']
    for a in c['assemblies']:
        people=[]
        for h in a['houses']:
            people.extend(n['name'] for n in h['resident_candidates'])
            if h['proprietor']:people.append(h['proprietor']+' (proprietor)')
        if a['interior_houses']:
            people += ['inside '+h['name']+': '+', '.join(n['name'] for n in h['resident_candidates']) for h in a['interior_houses']]
        dims=' × '.join(str(round(v)) for v in a['bounds']['size'])
        lines.append(f'| {a["title"]} | {", ".join(map(str,a["models"]))} | {dims} | {"; ".join(people) or "No fixed house NPC; see entry/prop records"} | {", ".join(str(h["id"]) for h in a["houses"]) or ", ".join(a["destinations"]) or "—"} |')
    lines+=['','## Important distinctions','',
      '- The walled reference is the **Dragon Hunter Camp**, whose keep enters `d16.blv`. The Dragon Cave and Naga Vault are different structures. Kalindra borrows the camp’s construction vocabulary, not its MM8 faction or quests.',
      '- Four two-person homes: Stormlance (Leane/Jaycin), Morningstar (Robert/Isram), Foestryke (Zelim/Herald), Ironfist (Sethine/Chadric). Morningstar is a compact 576×448 cottage: two occupants do not require a rich estate.',
      '- The six services inside the camp are individually modeled. Godric’s training hall stands outside that group and consists of parts54–55. Joined multi-destination blocks in Castleview are new compositions inspired by this kit; they are not a claim that Garrote already uses Ravenshore’s block pattern.',
      '- Parts35–36,37–38,39–40 are paired house wings. Part39 repeats an Otterton hint but belongs geometrically with Weldrick’s actual entrance on40. Count the actual destination once.',
      '- House-table Placeholder is not a named resident. Service proprietors and NPC-table occupants are reported separately.',
      '- Rendered village houses use green-grey masonry and rounded green roof tiles, with different trim and silhouettes; poor/med/rich model names do not establish different wall materials. A shared material family does not mean identical construction quality, footprint or roof height everywhere.',
      '- Exact native face dimensions, texture sizes, UV offsets and entrance normals remain in the JSON. Reference images are independently framed; use measurements for scale.',
      '', 'Rebuild data/docs with `python3 level_generation/scripts/catalogue_garrote.py`; render the recorded views through the parameterized `blender_building_catalogue.py` in a separate study scene, then run `python3 level_generation/scripts/review_garrote_catalogue.py` for contact sheets and source/render checks.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    cards=[]
    for r in c['models']:
        a=next(a for a in c['assemblies'] if a['id']==r['assembly'])
        body=[f'# {r["index"]:03d}: {r["name"]}','',f'![Native reference](../images/{r["index"]:03d}.png)','',
              f'Assembly: **{a["title"]}**; parts {a["models"]}.', '',a['note'],'',f'Family: {r["family"]}. Dimensions: '+ ' × '.join(str(round(v)) for v in r['bounds']['size'])+' native units.','',
              '## People and destinations','']
        for h in a['houses']:
            body.append(f'- {h["id"]}: {h["name"]}; proprietor: {h["proprietor"] or "not a separate named proprietor"}.')
            for n in h['resident_candidates']:body.append('  - '+n['name']+' — '+ '; '.join(t['title'] for t in n['topics']))
        if not a['houses']:body.append('No direct house destination. Interior contacts/transition destinations: '+json.dumps(a['interior_houses'],ensure_ascii=False))
        body+=['','## Materials','',*['- '+k+f': {v} faces' for k,v in r['materials'].items()]]
        (OUT/f'models/{r["index"]:03d}.md').write_text('\n'.join(body)+'\n')
        people=' '.join([h['name']+' '+str(h['proprietor'])+' '+' '.join(n['name'] for n in h['resident_candidates']) for h in a['houses']])
        cards.append(f'<article data-search="{html.escape((r["name"]+" "+r["family"]+" "+a["title"]+" "+people).lower(),quote=True)}"><a href="models/{r["index"]:03d}.md"><img loading="lazy" src="images/{r["index"]:03d}.png"></a><h3>{r["index"]:03d} {html.escape(a["title"])}</h3><p>{html.escape(r["family"])}</p><p>{html.escape(people)}</p><small>{html.escape(str([round(v) for v in r["bounds"]["size"]]))} units</small></article>')
    assembly_cards=[]
    for a in c['assembly_views']:
        assembly_cards.append(f'<article><img loading="lazy" src="images/assembly_{a["id"]}.png"><h3>{html.escape(a["purpose"])}</h3><p>Parts {a["models"]}</p></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Garrote Gorge catalogue</title><style>body{background:#20272a;color:#e0e7dc;font:15px system-ui;margin:25px}a{color:#add2da}h1{font-size:26px}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}article{background:#30393b;border:1px solid #56605c;padding:12px}img{width:100%;background:#1b2428}input{font:inherit;padding:10px;width:min(700px,95%)}small{color:#d0c39e}.wide{max-width:1400px}p{line-height:1.5}</style><h1>Garrote Gorge: buildings, residents, walls and keep</h1><p>Original reference only • 56 BModels • unique house destinations and physical assemblies counted separately.</p><p><a href="README.md">Inventory and caveats</a> · <a href="../../projects/mm5_castleview_kalindra/GARROTE_STYLE_MAPPING.md">Mapping to Castleview / Kalindra</a> · <a href="catalogue.json">Full measurements</a></p><h2>Whole assemblies</h2><section>ASSEMBLIES</section><h2>Native map placement</h2><img class="wide" src="images/placement.png"><h2>Material roles and equal-scale profiles</h2><img class="wide" src="images/texture_roles.png"><p><a href="images/contact_houses.jpg">House contact sheet</a> · <a href="images/contact_services.jpg">Service sheet</a> · <a href="images/contact_walls_keep.jpg">Wall / keep sheet</a> · <a href="images/contact_other.jpg">Other structures</a></p><img class="wide" src="images/materials.png"><img class="wide" src="images/height_profiles.png"><h2>Every native part</h2><input id="search" placeholder="Search resident, service, wall, house family…"><section id="parts">CARDS</section><script>document.querySelector('#search').oninput=e=>document.querySelectorAll('#parts article').forEach(a=>a.style.display=a.dataset.search.includes(e.target.value.toLowerCase())?'':'none');</script></html>'''
    (OUT/'index.html').write_text(page.replace('ASSEMBLIES',''.join(assembly_cards)).replace('CARDS',''.join(cards)))


def figures(c,native):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon,Rectangle
    from scipy.spatial import ConvexHull
    fig,ax=plt.subplots(figsize=(12,11));h=np.array(native['height_map']).reshape(128,128)*32
    ax.contour((np.arange(128)-64)*512,(64-np.arange(128))*512,h,levels=np.arange(0,8192,256),colors='#b9bea8',linewidths=.5)
    for a in c['assemblies']:
        q=np.concatenate([points(native['bmodels'][i])[:,:2] for i in a['models']]);hull=q[ConvexHull(q).vertices]
        color={'walls':'#7c8589','keep':'#a8afab','house':'#cfb990','service':'#c8a573'}.get(a['kind'],'#a6b4a0')
        # Individual projected faces preserve court voids in the camp outline.
        for i in a['models']:
            for f in native['bmodels'][i]['faces']:
                if f['attributes']&0x2000:continue
                vertices=np.array([[native['bmodels'][i]['vertices'][j][k] for k in ['x','y']] for j in f['vertex_indices']])
                ax.add_patch(Polygon(vertices,facecolor=color,edgecolor='#4f5d59',lw=.25))
        center=(q.min(0)+q.max(0))/2
        ax.text(*center,','.join(str(i) for i in a['models']),ha='center',fontsize=7,bbox=dict(facecolor='white',alpha=.65,edgecolor='none',pad=1))
    ax.set(xlim=(-28000,28000),ylim=(-28000,28000),aspect='equal',title='Garrote Gorge — original assemblies in native coordinates',xlabel='X native units',ylabel='Y native units');fig.tight_layout();fig.savefig(OUT/'images/placement.png',dpi=150);plt.close(fig)
    # All material swatches preserve their source aspect and report bitmap dimensions.
    keys=sorted(c['textures']);cols=6;w=1320;tileh=178
    sheet=Image.new('RGB',(w,((len(keys)+cols-1)//cols)*tileh+48),'#20272a');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    draw.text((16,12),'Native Garrote materials — keys / bitmap dimensions; swatches individually fitted',fill='white',font=font)
    for i,key in enumerate(keys):
        info=c['textures'][key];im=Image.open(ROOT/info['path']).convert('RGB');im.thumbnail((204,130),Image.Resampling.NEAREST)
        x,y=i%cols*220,48+i//cols*tileh;sheet.paste(im,(x+(220-im.width)//2,y))
        draw.text((x+6,y+135),key,fill='#e7ce94',font=font);draw.text((x+6,y+152),' × '.join(map(str,info['size'])),fill='white',font=font)
    sheet.save(OUT/'images/materials.png')
    samples=[a for a in c['assemblies'] if a['id'] in ['morningstar','ironfist','otterton','inn','training','camp_keep','camp_walls']]
    fig,ax=plt.subplots(figsize=(13,6));x=0
    for a in samples:
        lo=a['bounds']['min'];hi=a['bounds']['max'];ww=hi[0]-lo[0];hh=hi[2]-lo[2]
        ax.add_patch(Rectangle((x,0),ww,hh,facecolor='#aebaab',edgecolor='#344e43'))
        ax.text(x+ww/2,hh+80,a['id']+'\n'+str(round(hh))+' high',ha='center',fontsize=8)
        x+=ww+500
    ax.axhline(176,color='#36718c',lw=1,ls='--');ax.set(xlim=(-250,x),ylim=(0,1700),xlabel='Native width units; envelopes, not silhouettes',ylabel='Height above each assembly base',title='Equal physical scale — do not infer height from independently framed catalogue cards');fig.tight_layout();fig.savefig(OUT/'images/height_profiles.png',dpi=150);plt.close(fig)

if __name__=='__main__':build()
