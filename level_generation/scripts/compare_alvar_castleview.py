"""Record review-only Alvar alternatives against the existing Castleview premises reservations."""
import json
from catalogue_alvar import ROOT,OUT
from catalogue_ravenshore import source

PROJECT=ROOT/'level_generation/projects/mm5_castleview_kalindra'
# Each reference is an actual complete Alvar assembly. This is not a replacement of architecture_mapping.json.
CHOICES={
 'guild':('part_092','Alvar details','Use the polygonal guild vocabulary sparingly; author a lower main hall and membership wing, with Nool still outside.'),
 'forge':('four_shops','Mixed: Garrote workshop, Alvar shop frontage','Use one or two asymmetric shop bays and a Garrote-like working canopy; the whole four-way block is far too large.'),
 'training':('training','Alvar hall details','Shorten and narrow the hall to the reservation; keep the swimming annex separate. Its native buttressed flat roof is institutional, not a domestic default.'),
 'jail':(None,'Garrote','Keep the fortified masonry and controlled prison threshold; Alvar cottages are not the right structural reference.'),
 'monks_n':('part_066','Alvar','Shorten the long cottage and retain two study places under one roof; plain finish without an estate tower.'),
 'monks_s':('part_068','Alvar','A smaller gabled companion house with an offset door/garden side, not a mirrored duplicate.'),
 'bank':('part_065','Alvar','Compact finance house with a subordinate accounts room; one bank service and Rex retain their separate roles.'),
 'tavern':('profit_house','Alvar','New main guest room and lower entrance wing; reduce depth to preserve the street and shared court.'),
 'lodging':('withersmythe','Alvar composition only','Borrow unequal connected wings; omit the estate tower and reduce the footprint for shared modest lodging.'),
 'maps':('part_040','Alvar','Maintained square house with a map room and visible window/door rhythm; reserve remaining space for the shared frontage.'),
 'mayor':('part_049','Alvar','Wide low formal residence with an audience/office bay; restrained civic identity without another castle.'),
 'workyard':('part_011','Mixed','Borrow the timber canopy and loading details only; the native stables exceed this small yard reservation.'),
 'joe':('part_067','New makeshift shelter','Even the small Alvar cottage exceeds Joe’s 512-square envelope. Author a small lean-to/shelter; do not shrink doors or silently enlarge the lot.'),
 'ranger':('part_068','Alvar','Plain gabled cottage at normal door scale, with a practical garden-facing side.'),
 'herbalist':('part_067','Alvar','Small cottage with herb-drying details and planted court; quality comes from use and repair rather than a taller roof.'),
 'nadia':('part_067','Alvar','Worn small cottage with an offset entrance and sparse trim; preserve the west-gate lane.'),
 'diviners':('part_040','Alvar','Shared study house, two interior work areas, restrained arched-window details; no need for two exterior towers.'),
 'king':(None,'Garrote','Keep the fortified audience annex distinct from ordinary housing.'),
 'tower':('part_092','Mixed: Alvar arcane details, custom tower','Use the polygonal shaft/entry as a study only. Ellinger requires a much taller original composition with repeated normal-scale bays, not a stretched guild mushroom roof.'),
 'temple':('part_078','Alvar','The nave, lower side aisles and entrance porch suit Mok’s civic temple; create new symbols and preserve the taller planned nave.'),
 'crafts':('four_shops','Alvar organization only','Create two unequal shallow work bays for tailor/cobbler with distinct doors. Do not use the cross-shaped symmetric four-shop plan.'),
 'workers':('part_067','Alvar','One low cottage for Daron and Tolberti; shared occupancy is supported by the Garrote/Ravenshore study, not inferred from Alvar’s single-resident table.'),
 'keeper':('part_067','Alvar','Small shared cottage and newly fitted low kennel canopy; two residents do not imply a rich estate.'),
 'puzzle':('training','Alvar hall details','Broad low functional storehouse with two nine-chest bays and Dyson’s desk; no imported training service or native hall mesh.'),
}


def build():
    p=json.loads((PROJECT/'layout.json').read_text());c=json.loads((OUT/'catalogue.json').read_text())
    assemblies={a['id']:a for a in c['assemblies']};census={n['id']:n for n in p['census']}
    rows=[]
    for b in p['buildings']:
        if b['district']!='Castleview':continue
        key,preference,intent=CHOICES[b['id']];a=assemblies.get(key);fit=None
        if a:
            w,d,_=a['bounds']['size'];ew,ed=b['envelope']
            fit=(w<=ew and d<=ed) or (d<=ew and w<=ed)
        rows.append(dict(id=b['id'],title=b['title'],residents=[census[i]['name'] for i in b['npcIds']],
            quality=b['quality'],reservedEnvelope=b['envelope'],candidate=key,models=a['models'] if a else [],
            nativeAssemblyDimensions=a['bounds']['size'] if a else None,nativeEnvelopeFitsWithQuarterTurn=fit,
            preference=preference,newGeometryIntent=intent))
    assert len(rows)==24 and set(CHOICES)=={r['id'] for r in rows}
    data=dict(status='Design comparison only; existing Garrote architecture mapping remains the active proposal',
        recommendation='Alvar for most civilian houses and civic details; Garrote for walls, gates, jail and royal fortifications. All geometry newly authored.',
        fitMeaning='Axis-aligned exterior envelope comparison, allowing a 90-degree turn. Not door, foundation, street, courtyard, collision or room-capacity approval.',
        entries=rows,sources=[source(PROJECT/'layout.json'),source(OUT/'catalogue.json')])
    (PROJECT/'alvar_style_candidates.json').write_text(json.dumps(data,indent=2)+'\n')
    lines=['# Alvar versus Garrote Gorge for Castleview','',
        '[Alvar visual catalogue](../../catalogues/mm8_alvar/index.html) · [Side-by-side images](../../catalogues/mm8_alvar/images/alvar_vs_garrote.jpg) · [Measured candidate mapping](alvar_style_candidates.json) · [Existing Garrote proposal](GARROTE_STYLE_MAPPING.md)','',
        '**My recommendation is Alvar for most civilian houses, with Garrote retained for the city walls, gates, jail and royal fortifications.** Alvar better expresses the lived-in market town inside our Castleview walls: warm masonry, tiled roofs, compact cottages, service bays and larger shared establishments. This is a design judgement against our MM5 brief, not a claim that Alvar reproduces the original MM5 art.','',
        'This is a comparison before geometry authoring. It does not replace `architecture_mapping.json`, move buildings, change residents or change the approved minimap. Every resulting MM5 house/wall will still be newly constructed; the original BModels are rendered only as evidence.','',
        '## Where each reference is strongest','',
        '| Need in Castleview | Alvar | Garrote | Suggested use |','| --- | --- | --- | --- |',
        '| Ordinary residents and shared homes | Warm brown wall panels, brown roof tiles, gables/hips, chamfered small cottages and domestic steps | Green-grey masonry and green roofs give a more consistent stone-settlement character | Alvar for the main residential streets; retain the planned quality differences |',
        '| Shops and service houses | Parts 13–15 physically join four services; inns have a main body plus an entrance wing | More individually modeled camp service buildings | Alvar provides a stronger joined-premises reference, adapted into unequal bays |',
        '| Temple and mayor/civic buildings | Recognizable nave/aisles, low formal houses, merchant guild with portico and corner towers | Fortified halls and dressed stone details | Alvar for the temple and civic frontage; no need to make the mayor’s office another keep |',
        '| Walls, gates and jail | No complete city curtain/gate kit in Alvar; its fort and guildhouse are isolated compounds | Dragon Hunter Camp gives a measured curtain, real gate and fortified masses | Garrote remains stronger |',
        '| Castle Kalindra | Merchant guildhouse offers civic portico/tower composition, but is broad and only 1024 high | Camp keep provides fortification details but is also low, at 960 | New taller royal composition; Garrote structure, selective Alvar civic details |',
        '| Ellinger’s tower | A 1152-high polygonal guild tower gives an arcane accent, with a distinctive broad roof cap | Stone tower/gate details relate to the city’s fortifications | New tall tower; neither native silhouette is the finished design |',
        '| Fountain and small public spaces | Parts 79–80 form a complete 800×800 fountain with a low stone basin | Wells and camp utilities are useful smaller references | Author our 512-wide HP fountain using Alvar’s basin/cascade idea; preserve its planned interaction |','',
        '## Scale and occupancy findings','',
        '- All 34 residential assemblies have one initial NPC-table occupant in the current merged base; the merchant guild adds Bastian Loudrin. There are also 12 named service proprietors. Alvar’s architecture does not justify splitting our established shared households.',
        '- Garrote has 17 residential assemblies for 21 initial NPCs, including four two-person homes. The 576×448 Morningstar cottage demonstrates that two occupants do not require an estate.',
        '- Alvar’s visible residential entrance faces measure 128×256 native units throughout. That agrees with the door scale already proposed for Castleview. Keep these dimensions while adding/removing wall bays and changing roof composition.',
        '- Example Alvar exteriors: poor2 cottage 768×512×400; med1 gabled house 680×800×512; med3 house 736×768×576; rich1 low residence 1280×784×448; paired rich2 estate 1184×1296×896. Source family names are not a reliable height or wealth ranking.',
        '- The four-shop block is 2272×2272; our tailor/cobbler reservation is 1792×768. Its whole symmetric footprint is unsuitable, but its independently entered connected shop bays are useful.',
        '- Alvar’s training hall is 1152×1600; our training reservation is 1536×1000. It needs a new shorter/narrower arrangement. Its flat roof and buttresses also suit an institution better than a friendly cottage.',
        '- The Merchant Guildhouse is 2816×3008×1024; it fits within Kalindra’s 4096×3072 outer reservation in plan, but leaves little depth margin and is far below the proposed 2560 roof / 3584 principal towers. This is a massing reference, not a ready-made castle.',
        '- Havest Hall and nine other script house destinations have no active outdoor BModel entry in this source. They are listed separately in the catalogue; missing mesh bindings are not guessed onto neighbouring houses.','',
        '## Proposed references for all 24 town premises','',
        'The fit column compares only native exterior dimensions against the existing reservation, with a quarter-turn allowed. A yes does not certify streets, doors, room capacity or foundation fit. A no identifies geometry that must be recomposed; no uniform model scaling is proposed.','',
        '| MM5 premises / residents | Alvar reference parts | Reserved XY / native XYZ | Native envelope fits? | Proposed treatment |',
        '| --- | --- | --- | --- | --- |']
    for r in rows:
        refs=', '.join(f'[{i:03d}](../../catalogues/mm8_alvar/models/{i:03d}.md)' for i in r['models']) or 'Keep Garrote reference'
        dims=' × '.join(map(str,r['reservedEnvelope']))+' / '+(' × '.join(str(round(v)) for v in r['nativeAssemblyDimensions']) if r['nativeAssemblyDimensions'] else '—')
        fits='yes, dimensions only' if r['nativeEnvelopeFitsWithQuarterTurn'] else ('no; recompose' if r['candidate'] else '—')
        lines.append(f'| **{r["title"]}** — {"; ".join(r["residents"]) or "Service/interior contacts remain as planned"} | {refs} | {dims} | {fits} | {r["newGeometryIntent"]} |')
    lines+=['','## Keeping the combined style coherent','',
        'Use a deliberate material hierarchy: warmer Alvar domestic walls and brown tiled roofs within the town, heavier Garrote-style masonry at the perimeter and royal structures. Keep common door size, related mortar/stone tones, matching foundation courses and restrained trim. Do not alternate the two complete texture families randomly from house to house. The next visual blockout should compare both materials under the actual Castleview lighting before settling the wall/house transition.',
        '', 'Alvar’s common domestic family is `t05*`, including `t05a05` roof tiles and `t05a03` doors; Garrote’s is `t18*`. Native role swatches and exact UV/texel measurements are in their catalogues. Alvar buildings already share compatible temperate grass/dirt surroundings, but terrain tile-bank selection still follows the Brackenford calibration.',
        '', 'For Kalindra, prioritize the user’s taller friendly royal silhouette. Use a portico or a few corner/wing relationships from Alvar’s merchant guild if useful, then design the keep and towers at the actual reserved site. Avoid inheriting the guild’s low, broad roof or importing its MM8 signs, factions and dialogue.',
        '', 'The most informative first comparison blockout would contain one modest shared cottage, two unequal shop bays, the temple frontage, the 512-wide fountain and a short wall/gate segment. That exposes the domestic/fortified material relationship, ordinary door scale and shared frontage before extending the style across the city.',
        '', 'Rebuild this review with `python3 level_generation/scripts/compare_alvar_castleview.py` after updating the catalogue or MM5 reservations.']
    (PROJECT/'ALVAR_STYLE_COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print('Reviewed',len(rows),'premises;',sum(r['nativeEnvelopeFitsWithQuarterTurn'] is True for r in rows),'reference envelopes fit; geometry remains independently authored.')

if __name__=='__main__':build()
