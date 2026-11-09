"""Cover the remaining grey-water and plains-lava bank tiles with flat native-context patches."""
import csv
import json
import subprocess
import yaml
from common import P, ROOT, sha
from inventory import descriptor_index


def main():
    banks = json.loads((P/'liquids/banks_v2/build.json').read_text())['tiles']
    grids = json.loads((P/'effective_grids.json').read_text())
    inventory = json.loads((P/'effective_inventory.json').read_text())
    table = list(csv.DictReader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data.txt').open(),delimiter='\t'))
    report = dict(fixtures={})
    for family,map_id,base in [('shore_grey','out06','gdtyl'),('lava_plains','out04','plntyl')]:
        wanted = {r['name'] for r in banks if r['family']==family}
        native = grids[map_id]
        candidates = []
        for y in range(3,124):
            for x in range(3,124):
                covered = {n for row in native[y-3:y+4] for n in row[x-3:x+4]} & wanted
                if covered:
                    candidates.append((y,x,covered))
        pending = set(wanted);patches = []
        while pending:
            best = max(candidates,key=lambda r:len(r[2]&pending))
            assert best[2]&pending,(family,pending)
            patches.append(best);pending -= best[2]
        config = next(r for r in inventory['maps'] if r['id']==map_id)
        names = {}
        for raw in range(234):
            names.setdefault(table[descriptor_index(raw,config['master_tile'],config['lookup'])]['texture_name'].lower(),raw)
        grid = [[base]*128 for _ in range(128)];placements = {}
        for i,(y,x,covered) in enumerate(patches):
            top,left = 52+i//3*16,46+i%3*16
            for dy in range(7):
                for dx in range(7):
                    grid[top+dy][left+dx] = native[y-3+dy][x-3+dx]
            placements['patch%d'%i] = dict(row=top,col=left,native_map=map_id,native_row=y,native_col=x,
                                           covered_names=sorted(covered),
                                           pose=[(left+3.5-64)*512,(64-top-9)*512,3500,1.5707963268,-.96])
        folder = P/'fixtures/banks_extra_v1'/family;folder.mkdir(parents=True,exist_ok=True)
        for kind in ('map','scene','terrain','geometry'):
            data = yaml.safe_load((P/'fixtures/banks_v2/shore_dirt'/('out01.'+kind+'.yml')).read_text())
            if kind=='terrain':data['tile_map_hex'] = bytes(names[n] for row in grid for n in row).hex()
            elif kind=='scene':data['environment'].update(master_tile=config['master_tile'],tile_set_lookup_indices=config['lookup'])
            elif kind=='map':
                data.update(package_id='mm8:extra_bank_'+family,display_name='MM8 flat '+family)
                data.pop('source_fingerprint',None);data.pop('built_source_fingerprint',None)
            (folder/('out01.'+kind+'.yml')).write_text(json.dumps(data,indent=2)+'\n')
        with (folder/'build.log').open('w') as stream:
            subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(ROOT/'assets_dev'),
                            '--headless-build-map',str(folder/'out01.map.yml')],stdout=stream,stderr=subprocess.STDOUT,check=True)
        report['fixtures'][family] = dict(folder=str(folder.relative_to(P)),placements=placements,
                                         odm_sha256=sha(folder/'out01.odm'),covered_names=sorted(wanted))
        print(family,len(wanted),'names covered in',len(patches),'native patches',flush=True)
    report['script_sha256'] = sha(P/'prepare_extra_bank_fixtures.py')
    (P/'reports/bank_extra_fixtures.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
