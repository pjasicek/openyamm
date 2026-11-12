"""Copy the actors.yml entries that use a model into <out>: backup_actors.py <world> <model stem> <out yml>"""
import sys, re
world, stem, out = sys.argv[1:4]
text = open(f'assets_dev/worlds/{world}/models/actors.yml').read()
blocks = re.split(r'(?m)^(?=- descriptor:)', text)
keep = [b for b in blocks if f'models/{stem}.glb' in b]
open(out, 'w').write(''.join(keep))
print(len(keep), 'entries ->', out)
