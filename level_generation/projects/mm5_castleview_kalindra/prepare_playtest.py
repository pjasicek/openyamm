"""Prepare an isolated ordinary-game launcher and a fresh Castleview starting save."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

import yaml

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]


def prepare(stage, binary):
    stage=stage.resolve(strict=True)
    binary=binary.resolve(strict=True)
    owner=json.loads((stage/'mm5-stage.json').read_text())
    assert owner['project']=='mm5_castleview_kalindra'
    build=json.loads((PROJECT/'review/native/build.json').read_text())
    assert Path(build['stage']).resolve()==stage
    assets=stage/'assets_dev'
    native=assets/'worlds/mm5/maps/mm5_sw.odm'
    digest=hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest==build['nativeSha256'],'Staged map does not match the completed native build'
    for name,expected in build['sourceObjSha256'].items():
        assert hashlib.sha256((PROJECT/'implementation/source/models'/name).read_bytes()).hexdigest()==expected, (
            'Finish the native rebuild before preparing a starting save',name)
    assert build['actors']==0 and build['spawns']==0
    work=stage/'playtest'
    marker=work/'mm5-playtest.json'
    if work.exists() and any(work.iterdir()):
        assert json.loads(marker.read_text())['project']=='mm5_castleview_kalindra'
    work.mkdir(exist_ok=True)
    marker.write_text(json.dumps({'project':'mm5_castleview_kalindra'},indent=2)+'\n')
    settings=configparser.ConfigParser()
    settings.read(work/'settings.ini')
    for section in ['assets','startup','controls','debug','audio']:
        if not settings.has_section(section):settings.add_section(section)
    settings['assets']['root']=str(assets)
    settings['startup']['start_in_main_menu']='true'
    if 'control_scheme' not in settings['controls']:settings['controls']['control_scheme']='classic'
    for key,value in [('immortal','false'),('unlimited_mana','false'),('new_game_god_lich','false'),
                      ('movement_speed_multiplier','1')]:
        if key not in settings['debug']:settings['debug'][key]=value
    for key in ['sound_volume','music_volume']:
        if key not in settings['audio']:settings['audio'][key]='0'
    with (work/'settings.ini').open('w') as stream:settings.write(stream,space_around_delimiters=False)
    party_source=PROJECT.parent/'brackenford_greywatch/source/baseline_party.json'
    party=json.loads(party_source.read_text())
    scenario_id='mm5_castleview_start_'+hashlib.sha256(str(stage).encode()).hexdigest()[:12]
    scenario={'id':scenario_id,'world':'mm5','mode':'faithful','steps':[
        {'new_game_flow':{'start_map':'mm5_sw.odm','party':party}},
        {'save_game':'castleview_start'}]}
    scenario_path=work/'prepare_start.yml'
    scenario_path.write_text(yaml.safe_dump(scenario,sort_keys=False))
    launcher=stage/'play-mm5.sh'
    launcher.write_text('#!/bin/sh\nset -eu\ncd '+shlex.quote(str(work))+'\nexec '+shlex.quote(str(binary))+
                        ' --world mm5 "$@"\n')
    launcher.chmod(0o755)
    with (work/'prepare_start.log').open('w') as stream:
        subprocess.run([str(launcher),'--headless-run-scenario',str(scenario_path),
                        '--scenario-no-color'],cwd=work,stdout=stream,stderr=subprocess.STDOUT,check=True)
    saves=work/'saves'
    saves.mkdir(exist_ok=True)
    start=saves/'castleview_start.oysav'
    if start.exists():
        archive=work/'previous_starts'
        archive.mkdir(exist_ok=True)
        previous=archive/(hashlib.sha256(start.read_bytes()).hexdigest()+'.oysav')
        if not previous.exists():shutil.copy2(start,previous)
    shutil.copy2(Path('/tmp/openyamm_scenario_saves')/scenario_id/start.name,start)
    world = assets/'worlds/mm5'
    policy_source = PROJECT/'implementation/world_policy/events/common/cross_continents_common.lua'
    policy_runtime = world/'events/common/cross_continents_common.lua'
    assert policy_runtime.read_bytes() == policy_source.read_bytes(), 'Stale MM5 common-script policy'
    script_hashes = {str(path.relative_to(world)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted((world/'events').rglob('*.lua'))}
    minimap = world/'ui/maps/mm5_sw.provenance.json'
    map_presentation = json.loads(minimap.read_text()) if minimap.exists() else None
    report={'project':'mm5_castleview_kalindra','stage':str(stage),'launcher':str(launcher),
            'world':'mm5','map':'mm5_sw.odm','startSave':str(start),'nativeSha256':digest,
            'saveSha256':hashlib.sha256(start.read_bytes()).hexdigest(),
            'binary':str(binary),'binarySha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
            'worldScriptSha256':script_hashes, 'mapPresentation':map_presentation,
            'partyFixture':str(party_source.relative_to(ROOT)),
            'partyFixtureSha256':hashlib.sha256(party_source.read_bytes()).hexdigest(),
            'testParty':{'levels':[member['level'] for member in party['members']],
                         'gold':party['gold'],'food':party['food']},
            'usage':'Run the launcher, choose Load Game, and load castleview_start. '
                    'Ordinary subsequent saves and settings stay under this stage/playtest directory.',
            'limits':'Current environment checkpoint, not final package acceptance. '
                     'The fixture uses the established level-generation test party; no NPC/monster population is added. '
                     'Headless preparation is not visual proof of the loaded start.'}
    (work/'mm5-playtest.json').write_text(json.dumps(report,indent=2)+'\n')
    review=PROJECT/'review/playtest'
    review.mkdir(exist_ok=True)
    (review/'latest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',type=Path,default=Path('/tmp/openyamm-mm5-castleview'))
    parser.add_argument('--binary',type=Path,default=ROOT/'build/game/openyamm',
                        help='Executable used for both save preparation and ordinary play')
    args=parser.parse_args()
    prepare(args.stage,args.binary)
