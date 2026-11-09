"""Build isolated flat native fixtures over a copy of peasants enhanced."""
import configparser,csv,json,shutil,subprocess,yaml
from pathlib import Path
from build import P,T,ROOT,OUT,sha

def main():
    stage=Path('/tmp/openyamm-mm6-complete-terrain-review');stage.mkdir(exist_ok=True)
    enhanced=Path('/tmp/openyamm-sorpigal-peasants-playtest/enhanced')
    shutil.copy2(enhanced.parent/'openyamm',stage/'openyamm')
    fixtures=json.loads((P/'reports/flat_fixtures.json').read_text())
    table=list(csv.DictReader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data_3.txt').open(),delimiter='\t'))
    groups=[('dry',[234,342,162,774],['sand','snow','cracked']),('green',[306,270,162,774],['tropical','swamp'])]
    capture_poses={};maps={}
    for mode,lookup,families in groups:
        folder=P/'fixture'/mode;folder.mkdir(parents=True,exist_ok=True)
        names={table[i]['texture_name'].lower():i for i in range(90)}
        for slot,base in enumerate(lookup):
            for offset in range(36):names.setdefault(table[base+offset]['texture_name'].lower(),90+slot*36+offset)
        grid=[['6dirttyl']*128 for _ in range(128)]
        for row,family in enumerate(families):
            px,py=50,44+row*15
            for i,pad in enumerate(fixtures[family]):
                if i==1:
                    prefix=next(g['prefix'] for g in json.loads((P.parent/'inventory.json').read_text())['groups'] if g['id']==family)
                    # Close the exterior of the native dirt-hole test pad too.
                    # The 2D fixture assumes surrounding material; the native map is dirt.
                    for j in range(7):
                        grid[py-1][px+5+j]=prefix+('nw' if j==0 else 'ne' if j==6 else 'n')
                        grid[py+5][px+5+j]=prefix+('sw' if j==0 else 'se' if j==6 else 's')
                    for j in range(5):
                        grid[py+j][px+5]=prefix+'w';grid[py+j][px+11]=prefix+'e'
                for y,line in enumerate(pad):
                    for x,name in enumerate(line):grid[py+y][px+i*6+x]=name
            capture_poses[family]=dict(mode=mode,x=(px+5.5-64)*512,y=(64-py-8)*512-1500,z=4800,yaw=1.5707963268,pitch=-.96)
        for kind in ('map','scene','terrain','geometry'):
            data=yaml.safe_load((T/'mm6_new_sorpigal_transitions/fixture'/('oute3.'+kind+'.yml')).read_text())
            if kind=='terrain':data['tile_map_hex']=bytes(names[n] for row in grid for n in row).hex()
            if kind=='scene':data['environment']['tile_set_lookup_indices']=lookup
            if kind=='map':
                data.update(package_id='mm6:remaining_terrain_fixture_'+mode,display_name='Remaining MM6 terrain '+mode)
                data.pop('source_fingerprint',None);data.pop('built_source_fingerprint',None)
            (folder/('oute3.'+kind+'.yml')).write_text(json.dumps(data,indent=2)+'\n')
        with (folder/'build.log').open('w') as f:subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(ROOT/'assets_dev'),'--headless-build-map',str(folder/'oute3.map.yml')],stdout=f,stderr=subprocess.STDOUT,check=True)
        target=stage/mode
        if not target.exists():shutil.copytree(enhanced,target,symlinks=True)
        terrain=target/'assets_dev/worlds/mm6/terrain_x2';assert not terrain.is_symlink()
        for source in OUT.glob('*.png'):shutil.copy2(source,terrain/source.name)
        mapdir=target/'assets_dev/worlds/mm6/maps';assert not mapdir.is_symlink()
        excluded=target/'fixture_excluded_overlays';excluded.mkdir(exist_ok=True)
        for p in mapdir.glob('oute3.scene.*.yml'):shutil.move(str(p),excluded/p.name)
        for ext in ('odm','scene.yml'):shutil.copy2(folder/('oute3.'+ext),mapdir/('oute3.'+ext))
        config=configparser.ConfigParser(interpolation=None);config.read(target/'settings.ini')
        config['assets']['root']=str(target/'assets_dev');config['video_quality']['terrain']='x2'
        with (target/'settings.ini').open('w') as f:config.write(f)
        maps[mode]=sha(mapdir/'oute3.odm')
    (P/'captures').mkdir(exist_ok=True)
    seed=T/'mm6_new_sorpigal_dirt_fidelity/references/Dirt_View.oysav'
    for name,p in capture_poses.items():
        subprocess.run(['/tmp/sorpigal-transition-capture-save',str(seed),str(P/'captures'/(name+'.oysav')),*[str(p[k]) for k in ('x','y','z','yaw','pitch')],'empty-world','--fly-buff'],check=True,stdout=subprocess.DEVNULL)
    (P/'reports/review_stage.json').write_text(json.dumps(dict(stage=str(stage),binary_sha256=sha(stage/'openyamm'),map_hashes=maps,files={p.name:sha(p) for p in OUT.glob('*.png')},poses=capture_poses),indent=2)+'\n')
    print(stage)
if __name__=='__main__':main()
