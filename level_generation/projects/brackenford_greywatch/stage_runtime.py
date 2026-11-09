"""Install generated test content into an isolated development root, leaving original maps/tables untouched."""
import argparse
import csv
import json
import hashlib
from pathlib import Path
import shutil

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--directory',type=Path,default=Path('/tmp/openyamm-brackenford-greywatch'))
parser.add_argument('--package', type=Path, help='Install a verified content ZIP instead of regenerating registrations')
parser.add_argument('--no-project-state', action='store_true', help='Do not replace the authoring project staging pointer')
args=parser.parse_args()
if args.package:
    from content_package import read_verified
    package_manifest, package_entries = read_verified(args.package)
stage=args.directory.resolve()
owner=stage/'levelgen-stage.json'
if stage.exists() and any(stage.iterdir()) and not owner.exists():
    raise SystemExit('Refusing an existing directory without this project staging marker: '+str(stage))
stage.mkdir(parents=True,exist_ok=True)
owner.write_text(json.dumps({'project':'brackenford_greywatch','original_assets':str(ROOT/'assets_dev')},indent=2)+'\n')
assets=stage/'assets_editor_dev'
mounted_families={'icons','textures','sprites','audio','music','videos','terrain'}
def mirror(source,destination):
    destination.mkdir(parents=True,exist_ok=True)
    for child in source.iterdir():
        target=destination/child.name
        if child.is_dir() and child.name not in mounted_families:
            if target.is_symlink():
                target.unlink()
            mirror(child,target)
        elif not target.exists():
            if child.is_dir():
                target.symlink_to(child,target_is_directory=True)
            else:
                shutil.copy2(child,target)
mirror(ROOT/'assets_dev',assets)

def make_parent_writable(destination):
    """Split shared art-directory mounts only where the generated package contributes a file."""
    current = assets
    for part in destination.parent.relative_to(assets).parts:
        current = current / part
        if current.is_symlink():
            original = current.resolve(strict=True)
            current.unlink()
            current.mkdir()
            for child in original.iterdir():
                if child.is_dir():
                    shutil.copytree(child, current / child.name)
                else:
                    shutil.copy2(child, current / child.name)
        else:
            current.mkdir(exist_ok=True)
            # Migrate this project's earlier expanded mounts: PhysicsFS refuses file links inside a mount.
            for child in current.iterdir():
                if child.is_symlink() and child.is_file():
                    original = child.resolve(strict=True)
                    child.unlink()
                    shutil.copy2(original, child)

if args.package:
    for name, data in package_entries.items():
        destination = assets / name
        make_parent_writable(destination)
        if destination.is_symlink():
            destination.unlink()
        destination.write_bytes(data)
    registered = package_manifest['map_ids']
else:
    for source in (PROJECT/'runtime').rglob('*'):
        if source.is_file():
            destination=assets/source.relative_to(PROJECT/'runtime')
            make_parent_writable(destination)
            if destination.is_symlink():
                destination.unlink()
            shutil.copy2(source,destination)

    table=assets/'engine/data_tables/map_stats.txt'
    with (ROOT/'assets_dev/engine/data_tables/map_stats.txt').open(newline='') as stream:
        rows=list(csv.reader(stream,delimiter='\t'))
    assert not any(len(row)>2 and row[2].lower() in ('lg01.odm','lg02.blv') for row in rows)
    ids=json.loads((PROJECT/'source/ids.json').read_text())
    next_id=ids['maps']['lg02.blv']
    assert not any(row and row[0].isdigit() and int(row[0]) in ids['maps'].values() for row in rows), 'Map ID collision'
    reference=next(row for row in rows if len(row)>2 and row[2]=='d18.blv')
    indoor=list(reference)+['']*max(0,35-len(reference))
    indoor[0]=str(next_id); indoor[1]='Greywatch Vault'; indoor[2]='lg02.blv'
    indoor[5]='4'; indoor[6]='336'; indoor[9]='8'; indoor[10]='3'; indoor[11]='5'
    indoor[12]='0'; indoor[13:16]=['100','0','0']
    indoor[16:20]=['Human Mercenary','Human Mercenary','3','1-1']
    indoor[20:24]=['Human Mercenary','Human Mercenary','2','1-1']
    indoor[24:28]=['Human Mercenary','Human Mercenary','1','1-1']
    indoor[30]='level_generation'; indoor[31]='Original test dungeon; fixed actors, no random spawn duplication'
    indoor[32]=''; indoor[33]='-'; indoor[34]='mm8'
    rows.append(indoor)
    registered={'lg02.blv':next_id}
    if (PROJECT/'runtime/worlds/mm8/maps/lg01.odm').exists():
        reference=next(row for row in rows if len(row)>2 and row[2]=='out02.odm')
        outdoor=list(reference)+['']*max(0,35-len(reference))
        outdoor[0]=str(next_id+1); outdoor[1]='Brackenford'; outdoor[2]='lg01.odm'
        outdoor[5]='4'; outdoor[6]='336'; outdoor[9]='10'; outdoor[10]='3'; outdoor[11]='6'
        outdoor[12]='0'; outdoor[13:16]=['65','35','0']
        outdoor[16:20]=['Ogre Warrior','Ogre Warrior','3','4-6']
        outdoor[20:24]=['Ogre Mage','Ogre Mage','3','1-2']
        outdoor[24:28]=['Ogre Warrior','Ogre Warrior','2','4-6']
        outdoor[30]='level_generation'; outdoor[31]='Original grassland test region; geometry stage'
        outdoor[32]=''; outdoor[33]='-'; outdoor[34]='mm8'
        rows.append(outdoor)
        registered['lg01.odm']=next_id+1
    with table.open('w',newline='') as stream:
        csv.writer(stream,delimiter='\t',lineterminator='\n').writerows(rows)

    registry_path=PROJECT/'source/town_registry.json'
    if registry_path.exists():
        registry=json.loads(registry_path.read_text())
        for name,digest in registry['source_tables'].items():
            assert hashlib.sha256((ROOT/'assets_dev/engine/data_tables'/name).read_bytes()).hexdigest()==digest, (
                'Town source table changed; regenerate the inventory',name)
        for name,new_rows in registry['rows'].items():
            with (ROOT/'assets_dev/engine/data_tables'/name).open(encoding='cp1252',newline='') as stream:
                original=list(csv.reader(stream,delimiter='\t'))
            occupied={row[0] for row in original if row and row[0].isdigit()}
            assert all(row[0] not in occupied for row in new_rows), ('Town registry ID collision',name)
            with (assets/'engine/data_tables'/name).open('w',encoding='cp1252',newline='') as stream:
                csv.writer(stream,delimiter='\t',lineterminator='\n').writerows(original+new_rows)
        # Declare the MM8 continent for dynamic teacher notes; keep authored monster stats unbolstered.
        name='bolster_maps.txt'
        with (ROOT/'assets_dev/engine/data_tables'/name).open(encoding='cp1252',newline='') as stream:
            bolster=list(csv.reader(stream,delimiter='\t'))
        occupied={row[0] for row in bolster if row and row[0].isdigit()}
        for map_name,map_id in registered.items():
            assert str(map_id) not in occupied
            bolster.append([str(map_id),'Brackenford generation: '+map_name,'1','0','-','-','-','0','0','','-','-'])
        with (assets/'engine/data_tables'/name).open('w',encoding='cp1252',newline='') as stream:
            csv.writer(stream,delimiter='\t',lineterminator='\n').writerows(bolster)
    from configure_travel import configure
    configure(assets)
(stage/'settings.ini').write_text('[assets]\nroot='+str(assets)+'\n[audio]\nsound_volume=0\nmusic_volume=0\n'
    '[debug]\nimmortal=false\nunlimited_mana=false\nnew_game_god_lich=false\n'
    'movement_speed_multiplier=1\n')
if not args.no_project_state:
    (PROJECT/'staging.json').write_text(json.dumps({'stage':str(stage),'assets':str(assets),
        'map_stats':registered,'status':'isolated test installation',
        'package':str(args.package) if args.package else None},indent=2)+'\n')
print(stage)
