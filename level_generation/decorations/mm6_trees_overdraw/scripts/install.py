#!/usr/bin/env python3
"""Install one tree after its sheet was reviewed: checks that the installed source is still the baseline this pass
started from (work/<id>/installed.glb) or this pass's own last install (work/<id>/installed_export.sha256), so a change
by another session is never overwritten, that the gates passed or were accepted
(`gate.json`), keeps the baseline in backup_pre_overdraw/, then runs tools/install_model.py --engine over the same name.
Usage: install.py <id> [--accept-gate]"""
import hashlib, json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

tid = sys.argv[1]
spec = common.load(tid); W = spec['work']
src = os.path.join(common.REPO, 'assets_source', 'engine', 'models', spec['glb'])
base = os.path.join(W, 'installed.glb'); new = os.path.join(W, spec['glb'])
mine = os.path.join(W, 'installed_export.sha256')        # our own earlier install of this pass
cur = hashlib.sha256(open(src, 'rb').read()).hexdigest()
if open(src, 'rb').read() != open(base, 'rb').read() and not (os.path.exists(mine) and open(mine).read().strip() == cur):
    raise SystemExit(f'ABORT {src} differs from the baseline {base} and from our last install: compare first')
gate = json.load(open(os.path.join(W, 'gate.json')))
if not gate['pass'] and '--accept-gate' not in sys.argv:
    raise SystemExit('ABORT gates did not all pass (see gate.json); pass --accept-gate after reviewing')
win = subprocess.run([sys.executable, os.path.join(common.HERE, '..', 'mm8_3d', 'animated', 'scripts', 'check_winding.py'),
                      new], check=True, capture_output=True, text=True).stdout
if 'inverted closed parts: 0' not in win:
    raise SystemExit('ABORT winding: ' + win)
os.makedirs(os.path.join(common.HERE, 'backup_pre_overdraw'), exist_ok=True)
if not os.path.exists(os.path.join(common.HERE, 'backup_pre_overdraw', spec['glb'])):
    shutil.copy2(base, os.path.join(common.HERE, 'backup_pre_overdraw', spec['glb']))
subprocess.run([sys.executable, os.path.join(common.REPO, 'tools', 'install_model.py'), new, '--engine', '--name',
                spec['glb']], check=True, cwd=common.REPO)
open(mine, 'w').write(hashlib.sha256(open(src, 'rb').read()).hexdigest())
print('INSTALLED', tid, '->', src)
