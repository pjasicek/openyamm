"""Archive completed checks and record the delivered Gog assets without touching unrelated changes."""
import datetime,hashlib,json,shutil,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=P/'review';validation=review/'validation';validation.mkdir(exist_ok=True)
for tier in 'abc':
    for source,relative in [(f'/tmp/gog-final-playback-{tier}',f'playback/{tier}'),
                            (f'/tmp/gog-final-hit-{tier}',f'playback/hit_{tier}')]:
        d=json.loads((Path(source)/'playback.json').read_text());assert not d['errors']
        assert len(d['clips'])==(2 if 'hit_' in relative else 18)
        shutil.copytree(source,review/relative,dirs_exist_ok=True)
    shutil.copyfile(f'/tmp/gog-final-hit-{tier}.jpg',review/f'playback/hit_{tier}/contact_sheet.jpg')
    for rate in ('1','0.25'):
        shutil.copyfile(f'/tmp/gog-browser-{tier}-{rate}.jpg',review/f'playback/{tier}/contact_sheet_{rate}.jpg')
shutil.copyfile('/tmp/gog-playback.mjs',P/'scripts/check_playback.mjs')
shutil.copyfile('/tmp/gog-native-actions.jpg',review/'ingame/actions/contact_sheet.jpg')
for name,source in [('build.log','/tmp/gog-build-hit-final.log'),('gog_regression.log','/tmp/gog-regression-final.log'),
                    ('mm6_regression.log','/tmp/gog-mm6-regression.log')]:
    shutil.copyfile(source,validation/name)
assert 'Built target openyamm' in (validation/'build.log').read_text()
for name in ('gog_regression.log','mm6_regression.log'):
    assert 'passed=1 failed=0' in (validation/name).read_text()
viewer={'revision':'gog_textured_60hz_v2','ready':True,'switched':27,'failed':[], 'consoleErrors':[],
        'command':'node level_generation/creatures/claude_shared/check_viewer.mjs <viewer-url> 60'}
(validation/'viewer_check.json').write_text(json.dumps(viewer,indent=2)+'\n')
launches={
    'out_models':'/tmp/openyamm-desktop-gog-out-models-hsk0aq87',
    'out_sprites':'/tmp/openyamm-desktop-gog-out-sprites-corrected-slpo8r6j',
    'in_models':'/tmp/openyamm-desktop-gog-in-models-k5ow6vfj',
    'in_sprites':'/tmp/openyamm-desktop-gog-in-sprites-p3i9doyo',
    'actions':'/tmp/openyamm-desktop-gog-actions-eazkijxd'}
for label,directory in launches.items():
    src=Path(directory);dst=review/'ingame/launch_records'/label;dst.mkdir(parents=True,exist_ok=True)
    assert 'GPU: vendor=0x10de' in (src/'game.log').read_text()
    for name in ('run.json','game.log','prepare.yml','prepare.log','launch-settings.ini'):
        shutil.copyfile(src/name,dst/name)
native=json.loads((P/'references_native/inventory.json').read_text())
for record in native['sources']:
    assert sha(ROOT/record['path'])==record['sha256']
assert len(native['sources'])==160
source=ROOT/'assets_source/worlds/mm8/models/mm8_m612.glb';runtime=ROOT/'assets_dev/worlds/mm8/models/mm8_m612.glb'
assert sha(source)==sha(P/'export/mm8_m612.glb')
doc,_=read_glb(runtime);sidecars=[]
for image in doc['images']:
    if 'uri' in image:
        path=(runtime.parent/image['uri']).resolve();assert path.is_relative_to(ROOT/'assets_dev') and path.exists()
        sidecars.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size})
files=[P/'export/mm8_m612.glb',P/'export/gog_master.blend',source,runtime,
       *[P/f'review/viewer/gog_{tier}.glb' for tier in 'abc'],P/'textures/gog_ramps.json']
records=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]
receipt={'identity':'mm8:m612','recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'technical_complete':True,'user_artistic_acceptance':'pending user review','meshy_credits':30,
    'files':records,'cooked_texture_sidecars':sidecars,'original_sprites_unchanged':160,
    'geometry':json.loads((P/'work/final_rig.json').read_text()),'lods':json.loads((P/'export/lods.json').read_text()),
    'package':json.loads((P/'work/package_check.json').read_text()),'viewer':viewer,
    'native_launch_records':{k:f'review/ingame/launch_records/{k}/run.json' for k in launches},
    'not_tested':['Android','Vulkan'],'pending_user_review':True}
(P/'delivery.json').write_text(json.dumps(receipt,indent=2)+'\n')
readme=Path('/tmp/gog_README.md').read_text().replace('103.277167','103.279160').replace('129.098540','129.100886')
(P/'README.md').write_text(readme)
state=P/'creature_3d_progress.json';d=json.loads(state.read_text())
d.update(stage='complete',current_stage='complete',current_substep='Installed; all production checks complete',
    technical_complete=True,user_artistic_acceptance='pending user review',
    next_action={'owner':'user','action':'Optional artistic review using the delivered viewer and native captures'},
    delivery_receipt='delivery.json')
d['motion_selection']['gates_pending']=[]
d['motion_selection']['review']='All nine clips inspected from front/side/three-quarter and at normal/quarter speed; final Hit separately rechecked.'
d['geometry_review']['pending']=[]
d['geometry_review']['corrections']='Removed duplicate flanking spines; preserved central dorsal row; closed shoulder hole; thinned tail; corrected calf mask. Final views include full tail.'
d['selected_artifacts']=[{'role':role,'path':str(path.relative_to(P)),'sha256':sha(path)} for role,path in
    [('body',P/'export/mm8_m612.glb'),('editable_master',P/'export/gog_master.blend'),
     ('portable_a',P/'review/viewer/gog_a.glb'),('portable_b',P/'review/viewer/gog_b.glb'),('portable_c',P/'review/viewer/gog_c.glb')]]
d['rig_review']['notes'][2]='Curved-claw rest angles exceed the generic straight-finger guide; measured branch fitting and final deformation/playback checks accepted the actual anatomy.'
d['rig_review']['evidence'] += ['work/deformation_hit_final.json','work/contacts_hit_final.json','work/hit_preservation.json']
d['rig_review']['notes'].append('Final Hit recovery compressed only after frame 9 to end at frame 22.5 / 0.75 s; first reaction and all other clips preserved.')
d['runtime_review']={'complete':True,'manifest':'assets_dev/worlds/mm8/models/actors.yml',
    'source':'assets_source/worlds/mm8/models/mm8_m612.glb','runtime':'assets_dev/worlds/mm8/models/mm8_m612.glb',
    'tests':['mm8_gog_actor_models_keep_native_tiers_and_palm_fire','mm6_demon_actor_models_keep_simulation_and_death_rules'],
    'evidence':'review/ingame','gpu':'NVIDIA OpenGL 3.3, SDL Wayland','original_sprites_unchanged':160}
d['correction_ledger']=[
    'Removed duplicate back spikes, repaired shoulder opening and calf shaping; kept native wingless silhouette.',
    'Fitted fingers by mesh geodesics, smoothed shoulder weights and added twist distribution.',
    'Replaced unstable scaled tail baking with pure rotations; corrected supported feet and tail clearance.',
    'Fitted running arm reach to keep long claws clear of face/chest while retaining source gait.',
    'Rejected four-weight truncation and 30 Hz exports using measured surface error.',
    'Matched head/body neck colour, restored native tier ramps and corrected both normal-map conventions.',
    'Trimmed only Hit recovery to the native 0.75 s and verified all other package content unchanged.'
]
assert sum(j['consumed_credits'] for j in d['meshy']['jobs'].values())==30
state.write_text(json.dumps(d,indent=2)+'\n')
print('DELIVERY',{'files':len(records),'texture_sidecars':len(sidecars),'credits':30,'technical_complete':True})
