"""Bind the reviewed Garrote reference kit to independently authored MM5 premises."""
import json
from pathlib import Path
from build_plan import ROOT,OUT,read,write

# Source IDs are reference-only. Heights are proposed roof/parapet tops above local pads, never scale factors.
TOWN={
'guild':([16,41],640,'Small dressed guild hall plus a subordinate membership wing; keep Nool in the forecourt.'),
'forge':([19,20],640,'One forge hall, lean-to stock bay and working yard; combine construction details, not two MM8 shops.'),
'training':([54,55,25],704,'New shorter training hall and separate lesson annex; its reserved envelope is smaller than the original Godric assembly.'),
'jail':([9,13],768,'Low covered prison wing with slit windows and barred threshold; borrow masonry and guard-room details, not the whole keep.'),
'monks_n':([46,31],448,'Long modest masonry chapterhouse; two study stations inside one venue, no duplicated front doors.'),
'monks_s':([43,29],384,'Shorter companion chapterhouse with offset roof/entrance and a garden-facing side; avoid mirrored twins.'),
'bank':([41,37,38],576,'Dressed public banking room with a lower accounts wing and two identifiable doors.'),
'tavern':([21,22],704,'Unequal common-room and lodging wings around a service court; reserve Tanya and Gloria seats without inventing household ties.'),
'lodging':([24,46],640,'Long boarding house with a raised end; two rented rooms behind one dialogue destination.'),
'maps':([35,36,28],640,'New three-door L-shaped workshop court: Jethro household, Lydia lessons, Miles examinations; native paired wings are compositional evidence.'),
'mayor':([37,38,41],704,'Civic hall and smaller editorial wing; public forecourt, restrained dressed trim, no palace-scale office.'),
'workyard':([25,18],448,'Compact hiring office with an open timber work canopy; yard does the work of a larger building.'),
'joe':([7,18],304,'New lightweight roofed stall; borrow timber/canopy construction only, not a complete tent or stable.'),
'ranger':([29,27],448,'Modest masonry lodge, low roof, outdoor woodcraft practice; occupation does not imply wealth.'),
'herbalist':([31,25],448,'Compact house and lower drying shed inside the envelope; herbs and stock establish its role.'),
'nadia':([29,43],384,'Small worn masonry house with packed storage; reserve the remainder of the envelope for lean-to/roof clearance.'),
'diviners':([46,41],512,'Shared long house with a quiet discussion room and two distinct speakers; modest trim, no invented wizard palace.'),
'king':([13,15,9],896,'Covered fortified audience annex, discrete roof and controlled BLV entry; hostile use of the local kit does not define the town faction.'),
'tower':([9,13,16],3072,'Entirely new octagonal arcane tower; local stone base, vertical window rhythm and restrained roof detail. No camp tower mesh reuse.'),
'temple':([17,13],1024,'New apsed hall with a higher nave and lower service/contact wing; Mok symbols replace MM8 religious identity.'),
'crafts':([43,46,19],512,'Two work bays under an unequal roofline with independent tailor and cobbler doors; domestic/service details at normal scale.'),
'workers':([46,31],384,'One modest long shared house. Morningstar demonstrates that two residents need no estate; maintain a low roof and restrained trim.'),
'keeper':([31,25,18],448,'Small shared cottage with a lower kennel canopy; keep most of the household volume modest.'),
'puzzle':([54,55,18],704,'New broad low storehouse, two nine-chest bays plus moving-treasure bay and Dyson desk. Larger footprint is functional, not personal status.'),
}
COUNTRY={
'dreyfus':([7,17],384,'Temporary shelter with a small Mok shrine; no permanent copy of Sacred Steel.'),
'ruby':([19,29],448,'Compact workshop with covered sorting bench; ruby identity comes from stock/signage.'),
'emerald':([20,31],448,'Sibling workshop with a different yard opening and emerald stock; independent recipe.'),
'sapphire':([19,27],448,'Third workshop with a side loading canopy; independent sapphire recipe.'),
'diamond':([41,20],512,'Maintained workshop within the same small envelope; diamond cost is not evidence for a mansion.'),
'reger':([29],384,'Simple secluded stone hermitage with small study recess.'),
'falista':([],0,'Natural sanctuary; no fabricated house for a unicorn.'),
'luna':([31,25],384,'Small stone shelter beside animal-care clearing and three-place altar; keep landscape larger than hut.'),
'justine':([7,18],256,'New small canopy outside the pass gate; accessible before buying a pass.'),
'yog':([6,7,8],432,'Reference canvas construction only; new faction-specific camp grouping and negotiable audience space.'),
'vespar':([42,16],512,'Compact maintained retreat with restrained arcane details; no new guild service.'),
'kramer':([18,25],384,'Small office and repair canopy; wagons/loading lie in the separately reserved caravan yard.'),
'nibbler':([],0,'Natural shelter and quest-gated growing area, no human house.'),
'kalindra':([9,10,11,12,13,14,15],3584,'New royal composition: keep roof 2560, principal tower parapets 3584, lower wings 1024–1280; entry doors remain normal scale.'),
'western':([9,13],2816,'New tower with accessible roof transition and distinct locked ground route; source quest controls access, not a copied camp gate.'),
'mine':([0,1],384,'New geology-led portal; cave reference is limited to recess and threshold treatment, not dragon architecture.'),
 'troll_a':([],0,'Terrain hole with an authored rim and safe trigger/return treatment.'),
 'troll_b':([],0,'Separate terrain hole; retain its separate interior pocket.'),
 'troll_c':([],0,'Separate terrain hole; preserve fall and voluntary entry behavior.'),
'sewer_out':([9,43],384,'New low masonry drain with barred arch detail, fit to the actual riverbank.'),
'skyrope':([],0,'Rope and anchoring rock/tree structure; no new building.'),
}

PALETTE={
 'wall':['t18a01a','t18a02a','t18a02b'],
 'dressed_wall':['t18b01'],
 'corners':['t18a06','t18a07','t18b06','t18b07'],
 'roof':['t18a05'],
 'windows':['t18a04a','t18a04b','t18a04c','t18a04d','t18b04a','t18b04b','t18b04c'],
 'doors':['t18a03c','t18b03c'],
 'paired_barred_arch':['t18a03a','t18a03b','t18b03a','t18b03b'],
 'trim':['t18a11a','t18a11b','t18a11c'],
 'timber_canopies':['t68a10a','t68a11','t68a13mm'],
}

def build():
    p=read(OUT/'layout.json');cat=read(ROOT/'level_generation/catalogues/mm8_garrote_gorge/catalogue.json')
    specs={**TOWN,**COUNTRY};assert set(specs)=={b['id'] for b in p['buildings']}
    rows=[]
    for b in p['buildings']:
        ids,height,intent=specs[b['id']]
        occupants=[dict(id=c['id'],name=c['name'],venue=c['venue'],placement=c['placement'],role=c['role']) for c in p['census'] if c['building']==b['id']]
        ref=[dict(model=i,assembly=cat['models'][i]['assembly'],nativeSize=cat['models'][i]['bounds']['size']) for i in ids]
        spec=dict(referenceMap='mm8/out05.odm',referenceModels=ref,proposedTopAbovePad=height,
            status='design proposal; native geometry not authored',newComposition=intent,
            referenceOnly=True,doorSize=[128,256],quality=b['quality'],people=occupants)
        b['architecture']=spec
        rows.append(dict(id=b['id'],title=b['title'],district=b['district'],envelope=b['envelope'],**spec))
    walls=dict(referenceModels=[9,10,11,12],referenceHeight=1280,wallHeight=1024,towerTop=1792,
        thickness=256,towerOuterDiameter=768,gateClearOpening=[768,768],pedestrianDoor=[128,256],
        purpose='New irregular curtain following the proposed town perimeter; exposed outward faces, walkable/access-controlled gate and solid return corners.',
        status='Sizing targets; wall strips, tower pads and gate collision must be checked in native blockout.',
        modules=['straight curtain in several lengths','angled join','polygonal corner tower','gatehouse with real open passage','terminal/terrain footing','covered prison connection'])
    for f in p['features']:
        if f['id']=='town_wall':f['architecture']=walls
        if f['id']=='west_gate':f['architecture']=dict(referenceModels=[9,10,11,12],newComposition='Smaller west gate with one guard room and an unequal wall shoulder; same pass condition as south entrance. New composition in Garrote masonry.',opening=[512,768])
        if f['id']=='pass_gate':f['architecture']=dict(referenceModels=[9,10,11,12],newComposition='Two unequal guard volumes flanking a real open passage; pass check at its inner threshold.',opening=[768,768])
    p['architectureReference']=dict(catalogue='../../catalogues/mm8_garrote_gorge/index.html',policy='New authored geometry inspired by measured native references; no copied BModels.',palette=PALETTE,townWalls=walls)
    for key,v in p['construction'].items():
        if key in ['natural','makeshift']:continue
        v['walls']='Garrote t18 masonry; '+{'plain':'restrained corners and domestic windows','working':'service-building details and timber work canopies','worn':'modest masonry with weathering/repair props','maintained':'dressed base and organized frontage','civic':'dressed masonry, cornice and subordinate wings','fortified':'curtain/keep vocabulary with barred openings','arcane':'local masonry with a new tower silhouette','royal':'same local stone with taller royal keep and distinct court wings'}[key]
        v['roof']='t18a05 rounded green tiles; new roof shapes at native texel density'
    write('layout.json',p)
    write('architecture_mapping.json',dict(status='Reviewable design proposal',references=cat['sources'],palette=PALETTE,townWalls=walls,buildings=rows))
    lines=['# Garrote Gorge → Castleview and Kalindra','',
      '[Visual native catalogue](../../catalogues/mm8_garrote_gorge/index.html) · [Interactive MM5 wireframe](index.html) · [Structured mapping](architecture_mapping.json) · [Every original MM5 resident](RESIDENTS.md)','',
      'Garrote Gorge is the primary architectural reference. Ravenshore remains a measured comparison for spacing and joined destinations. All MM5 footprints, roof assemblies, walls and towers are to be authored anew. The catalogue renders original geometry only for study; it is not a donor mesh library for the new world.','',
      'The reference is the **Dragon Hunter Camp**, not the Dragon Cave or Naga Vault. Its keep leads to `d16.blv` and Sir Charles Quixote. Kalindra is the friendly royal seat in the MM5 story, with its original restoration/access conditions; using this stonework does not import the Dragon Hunters’ faction or conflict.','',
      '## Material and proportion rules','',
      '- Native renders show green-grey masonry, rounded green roof tiles, dressed corners, heavy arched door surrounds and horizontal trim. Asset names poor/med/rich describe model families, not proven resident wealth. The small homes are stone too.',
      '- Wall modules use t18a01a / t18a02a / t18a02b; dressed plinth treatment uses t18b01. Roofs use t18a05; corner strips use t18a06/07 or t18b06/07. Exact keys, bitmap dimensions and original per-face UV measurements are in the catalogue.',
      '- Domestic doors use t18a03c or t18b03c. The paired barred textures t18a03a/b and t18b03a/b suit secure arch details, not every friendly cottage. Use ordinary timber doors for domestic premises even when the original reference has a portcullis motif.',
      '- Keep ordinary doors at 128×256 and retain measured texel density when adding bays or floors. Never enlarge a whole model or stretch a door/window bitmap to make a royal building taller. The heights below are above each local pad, not absolute world Z.',
      '- Quality comes from repair state, window/trim choices, frontage organization, roof composition and function. Two residents do not require two houses or two exterior doors. Service proprietors remain separate from named NPC-table contacts.',
      '- The existing envelopes include roof/step/annex clearance. They are maximum planning reservations, not instructions to fill every rectangle. A 576×448 cottage can sit in a larger yard envelope. Explicit large institutions have actual room/workspace reasons.',
      '', '## Town assignment — all 24 physical assemblies','',
      '| Premises / people | Native study parts | Quality / proposed top | New composition |',
      '| --- | --- | --- | --- |']
    def people(r):
        return '; '.join(c['name']+(' (outside)' if c['placement']=='public exterior contact' else ' (restricted)' if c['placement']=='restricted interior' else '') for c in r['people']) or 'Contacts remain inside the attached BLV'
    for r in rows:
        if r['district']!='Castleview':continue
        links=', '.join(f'[{v["model"]:03d}](../../catalogues/mm8_garrote_gorge/models/{v["model"]:03d}.md)' for v in r['referenceModels'])
        lines.append(f'| **{r["title"]}** — {people(r)} | {links} | {r["quality"]}; {r["proposedTopAbovePad"]} | {r["newComposition"]} |')
    lines+=['','## Walls, gate and royal silhouette','',
      'The native camp wall assembly is 7,642×6,834×1,280; its keep is 2,816×2,560×960. The reference keep reads as a broad low hall. Copying or uniformly scaling it would not produce the requested Kalindra silhouette.','',
      '| New component | Proposed dimensions / height above pad | Purpose |','| --- | --- | --- |',
      '| Castleview curtain | 256 thick; top 1,024 | Enclose the irregular planned city; varying segment lengths follow its actual streets and terrain |',
      '| Town corner/gate towers | about 768 outer diameter; top 1,792 | Punctuate direction changes without making every corner identical |',
      '| South gate | clear opening 768 wide ×768 high; normal side doors | Real traversable opening with pass threshold; Justine remains outside |',
      '| West gate toward Kalindra | clear opening 512 wide ×768 high; 384-wide connecting lane | Same Castleview pass condition; human quarter connects to the western trade road without passing the south gate |',
      '| Kalindra main keep | footprint within the existing 4,096×3,072 castle reservation; top 2,560 | Higher royal hall with repeated normal-size floor/window bays |',
      '| Kalindra principal towers | top 3,584 | Recognizable landmark above the town wall and lower wings |',
      '| Kalindra lower wings | top 1,024–1,280 | Friendly court/service setting and forecourt enclosure |','',
      'These are blockout targets, not validated collision dimensions. Build straight curtains in several lengths, angled joins, polygonal corner towers, a real gate passage and terrain footings as newly authored components. Place towers at useful terrain/direction changes; do not turn the perimeter into a symmetric square or stamp evenly spaced towers along it.','',
      'Kalindra’s exterior should use an offset tall keep, two unequal subordinate wings, a legible entrance and a forecourt facing the regional approach. Its 4,096×3,072 reservation is for the castle massing, not a reduced copy of the whole 7,642×6,834 MM8 camp. Keep the forecourt outside that massing clear. Ellinger gets a narrower arcane silhouette; the Western Tower retains its separate roof arrival.','',
      'The restored state can show the complete friendly royal composition. The initial unavailable state needs its own presentation tied to the original MM5 restoration stages. Do not fabricate the sequence of missing wings or introduce a second permanent outdoor castle marker; precise stage visibility is deferred to the castle event conversion.','',
      '## Regional premises','',
      '| Destination / contact | Study parts | Proposed treatment |','| --- | --- | --- |']
    for r in rows:
        if r['district']=='Castleview':continue
        lines.append(f'| **{r["title"]}** — {people(r)} | '+(', '.join(str(v['model']) for v in r['referenceModels']) or 'Landscape / new prop')+f' | {r["newComposition"]} |')
    lines+=['','## Ground and first authoring sample','',
      'Use the existing calibrated temperate grass/dirt terrain family and native road-transition rules. Garrote supplies the compatible architectural colour vocabulary; final ground banks must be selected from the working Brackenford terrain calibration, not inferred from BModel textures. Preserve the MM5 river, Acid Pond and Xeen rim positions in the regional plan.','',
      'Start the native authoring pass with the guild/forge/training cluster, one paired modest residence and a short wall/gate corner. This exposes service frontage, shared occupancy, roof/door scale, ground transitions and the castle vocabulary before extending the whole city. Build Kalindra’s silhouette as a separate massing study once that kit reads correctly at eye height.','',
      'The current deliverable is the complete source-backed minimap and reference mapping. Runtime MM5 assets, final geometry, quest conversion and registry additions have not been generated.']
    (OUT/'GARROTE_STYLE_MAPPING.md').write_text('\n'.join(lines)+'\n')
    print('Architecture mapping:',len(TOWN),'town assemblies,',len(COUNTRY),'regional destinations')

if __name__=='__main__':build()
