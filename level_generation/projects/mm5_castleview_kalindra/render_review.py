"""Render deterministic SVG/PNG wireframes and a self-contained interactive review page."""
import html
import json
import math
from pathlib import Path
import textwrap
from build_plan import OUT, SOURCE, read, town_xy
from geography import SourceGeography,CLASS_COLORS

COLORS={'plain':'#d8c49a','working':'#c2a276','worn':'#a39378','maintained':'#dfcfa5','civic':'#edce88',
        'fortified':'#b9b7af','arcane':'#bfa9d9','royal':'#ebd596','natural':'#778a68','makeshift':'#b29c7e'}


def esc(s):return html.escape(str(s),quote=True)


def svg(plan, town):
    width,height=1920,1650
    bounds=(-9800,4700,-8600,9500) if town else (-24576,24576,-24576,24576)
    xmin,xmax,ymin,ymax=bounds
    scale=min(1420/(xmax-xmin),1420/(ymax-ymin));ox,oy=45,112
    def xy(p):return ox+(p[0]-xmin)*scale,oy+(ymax-p[1])*scale
    def poly(points):return ' '.join(f'{a:.1f},{b:.1f}' for a,b in map(xy,points))
    def rect(center,extent,fill,**kw):
        x,y=xy([center[0]-extent[0]/2,center[1]+extent[1]/2])
        return f'<rect x="{x:.1f}" y="{y:.1f}" width="{extent[0]*scale:.1f}" height="{extent[1]*scale:.1f}" fill="{fill}" '+ ' '.join(f'{k.replace("_","-")}="{v}"' for k,v in kw.items())+'/>'
    def label(p,s,size=13,color='#152322',anchor='middle'):
        x,y=xy(p);return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{color}" font-weight="bold">{esc(s)}</text>'
    def group(kind,id):return f'<g class="layer-{kind}" data-id="{esc(id)}" tabindex="0" role="button">'
    title='CASTLEVIEW • BUILDINGS, PEOPLE & QUEST SPACES' if town else 'CASTLEVIEW–KALINDRA • REGIONAL WIREFRAME'
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="DejaVu Sans, sans-serif">',
       '<rect width="1920" height="1650" fill="#eff0e6"/>',f'<text x="45" y="44" font-size="29" fill="#25392f" font-weight="bold">{esc(title)}</text>',
       '<text x="45" y="78" font-size="17" fill="#546557">Design v1 • native units • source evidence and adaptation are separate • no native map generated</text>',
       f'<defs><clipPath id="clip-{town}"><rect x="{ox}" y="{oy}" width="{(xmax-xmin)*scale}" height="{(ymax-ymin)*scale}"/></clipPath></defs>',
       f'<g clip-path="url(#clip-{town})">',rect([(xmin+xmax)/2,(ymin+ymax)/2],[xmax-xmin,ymax-ymin],'#b3be95')]
    geography=SourceGeography()
    for n in [3,4,7,8]:
        d=read(SOURCE/f'maps/dark_initial_state/maze{n:04}.dat.json')
        for y,row in enumerate(d['cells']):
            for x,c in enumerate(row):
                from build_plan import source_xy
                point=source_xy(n,x,y)
                out.append(rect(point,[1537,1537],CLASS_COLORS[geography(*point)]))
    # Source-sized water remains recognizable; subdued native-cell grid is a review aid, not intended terrain art.
    step=512 if town else 4096
    out.append('<g class="layer-grid" opacity=".14">')
    for x in range(math.ceil(xmin/step)*step,int(xmax)+1,step):
        a,b=xy([x,ymin]),xy([x,ymax]);out.append(f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" stroke="#334c36" stroke-width=".6"/>')
    for y in range(math.ceil(ymin/step)*step,int(ymax)+1,step):
        a,b=xy([xmin,y]),xy([xmax,y]);out.append(f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]}" stroke="#334c36" stroke-width=".6"/>')
    out.append('</g>')
    for f in plan['foliageGroups']:
        out.append(group('foliage','foliage:'+f['id']))
        cx,cy=f['center'];w,h=f['extent']
        points=[[cx-w*.48,cy-h*.3],[cx-w*.21,cy-h*.51],[cx+w*.24,cy-h*.35],[cx+w*.46,cy+h*.15],[cx+w*.15,cy+h*.45],[cx-w*.4,cy+h*.25]]
        out.append(f'<polygon points="{poly(points)}" fill="#547657" fill-opacity=".25" stroke="#52724c" stroke-dasharray="4 5"/>')
        if not town:out.append(label(f['center'],f['title'],11,'#314b31'))
        out.append('</g>')
    wall=next(f for f in plan['features'] if f['kind']=='wall')
    out+=['<g class="layer-buildings">',f'<polygon points="{poly(wall["polygon"])}" fill="#dad5b1" fill-opacity=".68" stroke="#6b6b5f" stroke-width="{wall["architecture"]["thickness"]*scale}"/>','</g>']
    for r in plan['roads']:
        out.append(group('roads','road:'+r['id']))
        out.append(f'<polyline points="{poly(r["points"])}" fill="none" stroke="#847355" stroke-width="{(r["width"]+96)*scale}" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append(f'<polyline points="{poly(r["points"])}" fill="none" stroke="#d8c69e" stroke-width="{r["width"]*scale}" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append('</g>')
    for b in plan['buildings']:
        if town and b['district']!='Castleview':continue
        out.append(group('buildings',b['id']))
        if 'frontage' in b:
            out.append(f'<polyline points="{poly(b["frontage"]["points"])}" fill="none" stroke="#d0bd98" stroke-width="{192*scale}"/>')
        out.append(rect(b['center'],b['envelope'],COLORS[b['quality']],stroke='#453f34',stroke_width='1.5'))
        if 'door' in b:
            for venue in b.get('venues',[{'door':b['door']}]):
                x,y=xy(venue['door']);out.append(f'<circle cx="{x}" cy="{y}" r="3.3" fill="#254f64"/>')
        if town:
            out.append(label(b['center'],b['label'],13))
            if b['npcIds']:out.append(label([b['center'][0],b['center'][1]-200],f'{len(b["npcIds"])} NPC',9))
        elif b['district']=='Countryside':out.append(label([b['center'][0],b['center'][1]+800],b['label'],12))
        out.append(f'<title>{esc(b["title"]+": "+b["purpose"])}</title></g>')
    symbols={'healing_fountain':'HP','gold_well':'$','stat_barrel':'B','entrance':'↓','chest':'C','puzzle_chest':'□','quest_item':'M','spring':'+','shrine':'S','warning':'!',
             'clue':'?','wreck':'W','camp':'!','gate':'G','bridge':'B','prop':'•','garden':'•','water':'≈','landmark':'P','challenge':'?'}
    for f in plan['features']:
        if f['kind']=='path':
            out.append(group('features',f['id'])+f'<polyline points="{poly(f["points"])}" fill="none" stroke="#ad9972" stroke-width="{192*scale}"/>'+ '</g>')
        if f['id']=='west_gate':out.append(label([f['point'][0]+700,f['point'][1]+240],'West gate',12))
        if f['id']=='public_orchard':out.append(label(f['point'],'Public orchard: 55 source trees / individual scatter later',12))
        if f['kind'] not in symbols:continue
        if not town and f['sources'] and f['sources'][0][0]==29:continue
        if not town and f['kind']=='puzzle_chest':continue
        out.append(group('features',f['id']))
        x,y=xy(f['point']);symbol=symbols[f['kind']]
        if f['kind']=='water':out.append(rect(f['point'],f['extent'],'#78a5af',stroke='#456a7a'))
        elif f['kind']=='bridge':out.append(rect(f['point'],f['extent'],'#d6bb8d',stroke='#4b4436'))
        if f['kind']=='puzzle_chest':
            out.append(rect(f['point'],[96,128],'#d8ac46',stroke='#846221'))
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="8" fill="#f3e8c9" stroke="#5e6449"/>')
            out.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" fill="#4c492e" font-size="12">{symbol}</text>')
        out.append(f'<title>{esc(f["title"])}</title></g>')
    for e in plan['encounters']:
        out.append(group('encounters','encounter:'+e['id']))
        out.append(rect(e['center'],e['extent'],'#bd6448',fill_opacity='.12',stroke='#964f3d',stroke_dasharray='7 4'))
        if town or e['id'] not in ['town_west','town_north','royal_guards']:
            out.append(label([e['center'][0],e['center'][1]+e['extent'][1]/2+160],e['sourceSpecies']+f' ×{e["proposedCount"]}',11,'#7d3028'))
        out.append('</g>')
    for s in plan['sourceSites']:
        if town and s['map']!=29:continue
        point=s['plannedPoint'];x,y=xy(point)
        out.append(f'<g class="layer-source" data-id="{s["id"]}" opacity=".7"><circle cx="{x}" cy="{y}" r="2.6" fill="#d939aa"/><title>{esc(s["id"])}</title></g>')
    for t in plan['travel']:
        out.append(label(t['arrival'],t['id']+' →',14,'#2c4f7b'))
    out+=['</g>',f'<text x="65" y="140" fill="#233f34" font-size="25">N ↑</text>']
    if not town:
        out.append(label([-2304,7800],'CASTLEVIEW • detail on town sheet',19))
        out.append(label([0,23000],'A3 / B3',14));out.append(label([0,-23000],'A4 / B4',14))
    # Right-hand index uses short lines; complete census remains in HTML/Markdown/JSON.
    x=1510;y=125
    out.append(f'<text x="{x}" y="{y}" font-size="20" font-weight="bold">'+('TOWN ASSEMBLIES' if town else 'REGIONAL DESTINATIONS')+'</text>');y+=34
    for b in plan['buildings']:
        if (b['district']=='Castleview')!=town:continue
        out.append(f'<g data-id="{b["id"]}"><rect x="{x}" y="{y-14}" width="14" height="14" fill="{COLORS[b["quality"]]}" stroke="#555"/>')
        short=b['title'].replace(' / ',' · ')
        for j,line in enumerate(textwrap.wrap(b['label']+' '+short,36)):
            out.append(f'<text x="{x+22}" y="{y+j*17}" font-size="13">{esc(line)}</text>')
        y+=max(1,len(textwrap.wrap(b['label']+' '+short,36)))*17+12
        if town:
            names=[c['name'].split(' the ')[0].split(' The ')[0] for c in plan['census'] if c['building']==b['id']]
            for line in textwrap.wrap(', '.join(names),43):
                out.append(f'<text x="{x+22}" y="{y-2}" font-size="10" fill="#596552">{esc(line)}</text>');y+=13
        out.append('</g>')
    y=max(y+20,1240)
    for line in ['Blue dots: reserved venue thresholds','Red dashed: proposed encounter space','Green dashed: bounded foliage group','G gate · ↓ sewer · C ordinary chest',
                 'M melon · + spring · P pyramid · B bridge','Pink dots: source bindings (optional overlay)',
                 'NPC counts include public contacts at a site.','House destinations and buildings differ.']:
        out.append(f'<text x="{x}" y="{y}" font-size="12" fill="#455949">{esc(line)}</text>');y+=23
    out.append('<text x="45" y="1570" font-size="15" fill="#425840">Landscape is a source-derived diagram. Streets, building envelopes and aggregate encounters are proposed placements.</text>')
    out.append('<text x="45" y="1595" font-size="15" fill="#425840">Town: rotated 180° to face the southern road. Interior gates and puzzle chambers retain access constraints in covered BLV spaces.</text>')
    sx,sy=xy([xmin+800,ymin+1100]);length=2048 if town else 8192
    out.append(f'<path d="M{sx},{sy} h{length*scale}" stroke="#354b3c" stroke-width="4"/><text x="{sx}" y="{sy-8}" font-size="12">{length} native units</text>')
    out.append('</svg>');return '\n'.join(out)


def build():
    p=read(OUT/'layout.json');svgs={}
    import gi
    gi.require_version('Rsvg','2.0')
    from gi.repository import Rsvg
    import cairo
    for name,town in [('region_wireframe',False),('castleview_wireframe',True)]:
        s=svg(p,town);svgs[name]=s;(OUT/f'{name}.svg').write_text(s)
        # Static exports hide the dense source-mechanics overlay.
        static=s.replace('<svg xmlns=', '<svg xmlns=',1).replace('<defs>', '<style>.layer-source{display:none}</style><defs>',1)
        handle=Rsvg.Handle.new_from_data(static.encode());surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,1920,1650)
        handle.render_cairo(cairo.Context(surface));surface.write_to_png(str(OUT/f'{name}.png'))
    entities=[]
    for b in p['buildings']:
        entities.append(dict(b,people=[c for c in p['census'] if c['building']==b['id']]))
    entities+=p['features']
    for key,prefix in [('roads','road:'),('encounters','encounter:'),('foliageGroups','foliage:')]:
        entities += [dict(e,id=prefix+e['id']) for e in p[key]]
    entities+=p['sourceSites']
    data=json.dumps(entities,ensure_ascii=False).replace('<','\\u003c')
    template='''<!doctype html><html lang="en"><meta charset="utf-8"><title>MM5 Castleview–Kalindra layout review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#eff0e6;color:#263b30;font:15px system-ui}header{padding:18px 24px;border-bottom:1px solid #adb9a0}h1{font-size:23px;margin:0 0 8px}button,input{font:inherit;padding:7px;border:1px solid #a2b092;background:#fbfcf7;border-radius:4px}nav{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:14px}main{display:grid;grid-template-columns:minmax(600px,1fr) 390px;height:calc(100vh - 150px)}#canvas{overflow:auto}#canvas svg{width:1500px;height:auto}aside{padding:16px;overflow:auto;background:#fbfcf7;border-left:1px solid #adb9a0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}.item{display:block;width:100%;text-align:left;margin:5px 0}a{color:#356d87}.layer-source{display:none}[data-id]{cursor:pointer}[data-id]:hover{filter:brightness(1.12)}.selected{filter:drop-shadow(0 0 4px #fff) drop-shadow(0 0 3px #315f95)}small{color:#60715c}#details h2{font-size:19px}.pill{background:#e6eadb;padding:4px 7px;border-radius:4px;display:inline-block;margin:3px}details{margin:10px 0}#results{max-height:240px;overflow:auto}@media(max-width:950px){main{display:block;height:auto}aside{border-top:1px solid #aaa}#canvas{height:65vh}}</style>
<header><h1>MM5 · Castleview–Kalindra · layout review v1</h1><small>24 town assemblies · 48 source NPC sites + 6 services · source-linked layout, no live world changes.</small>
<nav><button id="town">Town detail</button><button id="region">Whole SW region</button><label>Zoom <input id="zoom" type="range" min="800" max="3200" value="1500"></label>
<label><input type="checkbox" data-layer="encounters" checked>Encounters</label><label><input type="checkbox" data-layer="foliage" checked>Foliage</label><label><input type="checkbox" data-layer="features" checked>Interactions</label><label><input type="checkbox" data-layer="source">Source bindings</label><label><input type="checkbox" data-layer="grid" checked>Grid</label>
<a href="README.md">Design notes</a><a href="landscape/index.html">Heightmap / decorations</a><a href="landscape/buffer.html">Full terrain buffer (authoring)</a><a href="GARROTE_STYLE_MAPPING.md">Garrote mapping</a><a href="../../catalogues/mm8_garrote_gorge/index.html">Visual catalogue</a><a href="../mm5_world_feasibility/plans/029.png">Original MM5 town</a><a href="RESIDENTS.md">Residents / venues</a><a href="reference_occupancy.json">MM8 occupancy evidence</a></nav></header>
<main><div id="canvas"></div><aside><input id="search" placeholder="Find NPC, teacher, house, source…" style="width:100%"><div id="results"></div><div id="details"><h2>Select a building or marker</h2><p>Click a footprint, map label or search result. Multiple people and service destinations can share one physical assembly.</p><p>Quality is an architectural proposal based on function, not a claim about the character’s wealth.</p></div></aside></main>
<template id="town-svg">TOWN_SVG</template><template id="region-svg">REGION_SVG</template>
<script>const entities=ENTITY_DATA;const lookup=new Map(entities.map(e=>[e.id,e]));const canvas=document.querySelector('#canvas');
function layers(){document.querySelectorAll('[data-layer]').forEach(c=>canvas.querySelectorAll('.layer-'+c.dataset.layer).forEach(g=>g.style.display=c.checked?'inline':'none'));}
function show(kind){canvas.replaceChildren(document.querySelector('#'+kind+'-svg').content.cloneNode(true));canvas.querySelector('svg').style.width=document.querySelector('#zoom').value+'px';layers();}
function text(tag,s){let e=document.createElement(tag);e.textContent=s;return e;}
function select(id){const e=lookup.get(id);if(!e)return;canvas.querySelectorAll('.selected').forEach(n=>n.classList.remove('selected'));canvas.querySelectorAll('[data-id]').forEach(n=>{if(n.dataset.id===id)n.classList.add('selected')});const panel=document.querySelector('#details');panel.replaceChildren(text('h2',e.title||e.name||e.id));panel.append(text('p',e.purpose||e.disposition||''));if(e.quality)panel.append(text('p','Construction: '+e.quality+' (design inference).'));if(e.architecture){panel.append(text('p','Garrote reference parts: '+(e.architecture.referenceModels||[]).map(v=>typeof v==='number'?v:v.model).join(', ')));panel.append(text('p',e.architecture.newComposition||e.architecture.purpose||''));}if(e.people){for(const person of e.people){let d=document.createElement('details');d.append(text('summary',person.name+' — '+person.role));d.append(text('p','Venue: '+person.venue+'; '+person.placement));for(const t of person.dialogue)d.append(text('p','Source text '+t.index+': '+t.text));panel.append(d)}}let d=document.createElement('details');d.append(text('summary','Coordinates, source links and structured record'));d.append(text('pre',JSON.stringify(e,null,2)));panel.append(d);}
canvas.addEventListener('click',ev=>{const el=ev.target.closest('[data-id]');if(el)select(el.dataset.id)});canvas.addEventListener('keydown',ev=>{if(ev.key==='Enter'){const el=ev.target.closest('[data-id]');if(el)select(el.dataset.id)}});
document.querySelector('#town').onclick=()=>show('town');document.querySelector('#region').onclick=()=>show('region');document.querySelector('#zoom').oninput=ev=>canvas.querySelector('svg').style.width=ev.target.value+'px';document.querySelectorAll('[data-layer]').forEach(c=>c.onchange=layers);
document.querySelector('#search').oninput=ev=>{const q=ev.target.value.toLowerCase();const list=document.querySelector('#results');list.replaceChildren();if(q.length<2)return;for(const e of entities.filter(e=>JSON.stringify(e).toLowerCase().includes(q)).slice(0,35)){const b=text('button',e.label?e.label+' '+e.title:e.title||e.name||e.id);b.className='item';b.onclick=()=>select(e.id);list.append(b)}};show('town');</script></html>'''
    template=template.replace('TOWN_SVG',svgs['castleview_wireframe']).replace('REGION_SVG',svgs['region_wireframe']).replace('ENTITY_DATA',data)
    (OUT/'index.html').write_text(template)
    print('Rendered two wireframes and self-contained interactive review.')

if __name__=='__main__':build()
