"""Measure repeated architectural forms separately from services and multipart mesh partitions."""
from collections import defaultdict
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LEVEL=ROOT/'level_generation'
PROJECT=LEVEL/'projects/brackenford_greywatch'
reference=json.loads((LEVEL/'catalogues/mm8_ravenshore/catalogue.json').read_text())
plan=json.loads((PROJECT/'outdoor_plan.json').read_text())
families=defaultdict(list)
for model in reference['models']:
    family=model['family']
    if family.startswith(('delf_','hcleric_','ogre_')):
        families[family].append(model['index'])
    elif model['name'].startswith('02dock_wh2'):
        families['dock_wh2'].append(model['index'])
assert sum(map(len,families.values()))==44 and len(families)==13
registry=json.loads((PROJECT/'source/town_registry.json').read_text())
assert {h['building'] for h in registry['houses']}=={b['id'] for b in plan['buildings']}
# Classify by the actual house role, including appended infill homes with different name prefixes.
# The civic manor is the deliberate unique residential landmark, outside the ordinary kit.
ordinary_ids={h['building'] for h in registry['houses']
              if h['service_type']=='House' and h['building']!='civic_hall'}
ordinary=[b for b in plan['buildings'] if b['id'] in ordinary_ids]
generated=defaultdict(list)
for b in ordinary:generated[b['form']].append(b['id'])
houses={h['id']:h for m in reference['models'] for s in m['services'] for h in s['houses']}
land_houses={i:h for i,h in houses.items() if h['type']!='Boats'}
assert len(land_houses)==59
physical={b.get('shared_block',b['id']) for b in plan['buildings']}
result=dict(method='Architectural form, collapsing rotated copies, source suffixes and multipart assemblies; not exact mesh hashes.',
    reference=dict(ordinary_instances=44,ordinary_forms=13,instances_per_form=44/13,families=dict(families),
        land_house_service_destinations=59,physical_house_service_assemblies=51,whole_building_forms=20,
        whole_building_instances_per_form=51/20,
        whole_building_derivation='44 ordinary + Oracle + Sanctum + Dancing Ogre + Adventurer’s Inn + NE/NW/SE service blocks. Forms: 13 ordinary + those 7 unique assemblies. Excludes boats and dungeon exteriors.'),
    generated=dict(logical_house_service_doors=len(plan['buildings']),physical_house_service_assemblies=len(physical),
        whole_building_forms=len({b['form'] for b in plan['buildings']}),
        ordinary_instances=len(ordinary),ordinary_forms=len(generated),instances_per_form=len(ordinary)/len(generated),
        families=dict(generated)))
out=PROJECT/'review/house_variety';out.mkdir(parents=True,exist_ok=True)
(out/'house_variety.json').write_text(json.dumps(result,indent=2)+'\n')
lines=['# House repetition and variety calibration','',
    'Count a physical architectural form once regardless of cardinal rotation or source suffix. Count an assembled',
    'service block once even when several BModels/doors form it. A material tint or small size adjustment does not',
    'automatically create another form. This is an architectural classification, not a byte-identical mesh count.','',
    '| Category | Ravenshore | Revised Brackenford |','| --- | --- | --- |',
    f'| Ordinary residence / teacher / storage instances | 44 | {len(ordinary)} |',
    f'| Repeated ordinary forms | 13 | {len(generated)} |',
    f'| Ordinary instances per form | 3.38 | {len(ordinary)/len(generated):.2f} |',
    f'| Land house/service destinations | 59 | {len(plan["buildings"])} |',
    f'| Physical house/service assemblies | 51 | {len(physical)} |',
    f'| Whole-building architectural forms | 20 | {result["generated"]["whole_building_forms"]} |',
    f'| Physical assemblies per form, including landmarks | 2.55 | {len(physical)/result["generated"]["whole_building_forms"]:.2f} |','',
    'Ravenshore has 45 House-type destination records: 44 ordinary house/storage instances plus the unique Oracle.',
    'Its other 14 land destinations are services. Two boat destinations are excluded. Six dungeon exterior complexes',
    'are also excluded from the house ratio. Their BModel part counts are not house counts.','',
    'The 51 physical assemblies are 44 ordinary houses, Oracle, Sanctum, Dancing Ogre, Adventurer’s Inn and three',
    'joined service blocks (north-east, north-west, south-east). The latter seven add seven distinct whole-building',
    'compositions to the 13 ordinary forms. The Merchant House south-west block is a dungeon exterior.','',
    f'Brackenford has {len(plan["buildings"])} logical service/resident doors in {len(physical)} physical buildings/blocks.',
    'Weapon and armor shops share Smiths Row. Ordinary roles come from the house registry, excluding the civic manor;',
    'this includes the five added court/well-lane homes. Services reuse some ordinary forms and add landmark compositions.',
    'The driver accepted this infill revision. Use [Accepted outdoor calibration](OUTDOOR_CALIBRATION.md) for future maps;',
    'the earlier facade-stage 15/5 ratio remains historical evidence, not the current count or an exact quota.','',
    '## Native repeated forms','', '| Form | Instances | BModels |','| --- | --- | --- |']
for family,ids in sorted(families.items()):lines.append(f'| `{family}` | {len(ids)} | {ids} |')
lines+=['','## Generated repeated forms','', '| Form | Instances | Buildings |','| --- | --- | --- |']
for family,ids in sorted(generated.items()):lines.append(f'| `{family}` | {len(ids)} | {", ".join(ids)} |')
lines+=['','## Apply to future generation','',
    'Choose a reference settlement and report both ordinary-house repetition and whole-building/service composition.',
    'For a comparable Ravenshore-like brief, roughly three to four ordinary houses per recurring form is a useful start,',
    'with several common forms and a few rarer ones. The reference and accepted example are evidence, not universal quotas.',
    'Make landmarks and joined service blocks deliberate exceptions. Preserve a coherent texture kit and measured',
    'facade scale across variants. Inspect a street and a town overview: a ratio alone cannot establish visual quality.',
    'Do not count a changed rotation, extra chimney, window decal or arbitrary material swap as useful architectural variety.','',
    '[Catalogue](catalogues/mm8_ravenshore/README.md) · [Calibration](VISUAL_CALIBRATION.md) ·',
    '[Current measured membership](projects/brackenford_greywatch/review/house_variety/house_variety.json)','',
    'Regenerate with `python3 level_generation/scripts/measure_house_variety.py`. Sources are the Ravenshore catalogue',
    'and current `outdoor_plan.json` plus `source/town_registry.json`; native families and semantic IDs make counts reviewable.',
    'Historical facade evidence remains in the project’s `review/facade_revision/house_variety.json`.']
(LEVEL/'HOUSE_VARIETY.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'reference_ordinary':[44,13], 'generated_ordinary':[len(ordinary),len(generated)],
                  'reference_all':[51,20], 'generated_all':[len(physical),len({b['form'] for b in plan['buildings']})]}))
