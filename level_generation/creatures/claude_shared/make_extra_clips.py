#!/usr/bin/env python3
"""Write a Blender-route MM9 project's dropped-clip scripts (run2-clips-groupC, 2026-10-31) from a JSON spec:
scripts/extra_clips_blend.py (shim over claude_shared/mm9_extra_clips_blend.py) and scripts/extra_clips.sh.

    make_extra_clips.py <project dir> <spec.json>

Spec keys:
  blend      the source blend build_export.py opens (project-relative)
  rig        armature object name (default MM9_Rig)
  roles      {Clip: [[MM9 sources], loop]} new clips AND Ctl_* controls
  holds      {Hold: Role} one-second holds of a role's last pose (temporary Dead2 / Ctl_Dead for --ground-death)
  hold_mode  'rec' (the last key, C.hold_action) or 'eval' (the last frame evaluated, as most build_export.py Deads)
  new        clips grafted onto the export (the rest are controls or temporaries)
  controls   {Ctl_X: AcceptedClip} compared with the installed clips after the control floor passes
  floor_ctl  list of floor passes for the controls, each a command line after "<in> <out>" (floor_fix.py unless the
             pass starts with "SMOOTH ", which runs the project's scripts/floor_smooth.py; "RAW <command>" is put in
             as written, with {in}, {out} and {start} (the chain's first input) replaced)
  floor_new  the same for the new clips
  post_code  optional lines of Python defining post(rig, report, C): the project's build_export.py steps on the role
             actions after build_role_clips (e.g. helper bones copying MM9 rotations); runs before the export
  name       export name (default: the project folder without _claude); suffix: script/before-file suffix for a
             second body in one project (scripts/extra_clips_pod.sh, work/pre_clips_export_pod.glb)
  prep_code / pre_export_code  optional lines defining prep(rig) (after opening, before the clips) and
             pre_export(rig) (just before the export); post_first: run post before the holds (holds then copy the
             post-processed last pose, as a build_export.py whose Dead follows its post steps)
  exported_as  {role: name} for a role the shim renames before the export (a control that must carry an accepted
             clip's name while the project's post steps run)
  notes      comment lines put at the top of both scripts (why, findings)
"""
import json
from pathlib import Path
import sys

BLEND_TEMPLATE = '''"""Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export leaves out with this
project's clips_mm9.py (via claude_shared/mm9_extra_clips_blend.py) from the source blend build_export.py opens
({blend}), and export the armature with them. Ctl_* are controls rebuilt from accepted clips' sources (compared with the
installed clips, never grafted); holds are temporary corpses for the floor pass. Written by
claude_shared/make_extra_clips.py from scripts/extra_clips.json; run by scripts/extra_clips.sh.
{notes}"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'claude_shared'))
import mm9_extra_clips_blend as X

ROLES = {roles}
{post_code}
{prep_code}
{pre_export_code}
X.main(HERE, ROLES, rig_name={rig!r}, holds={holds!r}{post_arg}, hold_mode={hold_mode!r}{extra_args})
'''

SH_TEMPLATE = '''#!/usr/bin/env bash
# Dropped MM9 clips (run2-clips-groupC, 2026-10-31): build the MM9 clips the accepted export left out with this
# project's own clips_mm9.py (scripts/extra_clips_blend.py on {blend}, the blend build_export.py opens), graft them into
# a copy of the accepted export, floor them with the passes build_runtime.sh gives accepted clips of the same kind, then
# graft only the new clips onto the accepted export with claude_shared/graft_clips.py, so meshes, LODs, variants and
# accepted clips stay byte for byte. Ctl_* controls go through the same steps and are compared with the installed clips.
# Written by claude_shared/make_extra_clips.py from scripts/extra_clips.json.
{notes}# Usage: TOK=<lease token> scripts/extra_clips{sfx}.sh   (work/pre_clips_export{sfx}.glb = the export before this step)
set -euo pipefail
cd "$(dirname "$0")/.."
here="$PWD"; repo="$(cd ../../.. && pwd)"; name={name}
G=../claude_shared/gltf_venv/bin/python; F=../claude_shared/floor/floor_fix.py; FS=scripts/floor_smooth.py
GR=../claude_shared/graft_clips.py
Q() {{ "$@" 2>&1 | grep -v "Unexpected value\\|RuntimeWarning" ; }}
E=${{EXPORT:-work/pre_clips_export{sfx}.glb}}
(cd "$repo" && tools/run_creature_blender.sh --token "$TOK" level_generation/creatures/$(basename "$here")/scripts/extra_clips_blend{sfx}.py \\
  "$here/{blend}" "$here/work/extra_raw.glb" "$here/work/clips_extra.json" | tail -1)
Q $G $GR $E work/extra_raw.glb work/g0.glb {graft_all} | tail -1
{floor_ctl}{compare}{floor_new}Q $G $GR $E work/gn.glb export/$name.glb {graft_new} | tail -1
Q $G ../claude_shared/graft_byte_check.py $E export/$name.glb
'''


def passes(chain, start, final):
    lines, cur = [], start
    for k, p in enumerate(chain):
        out = final if k == len(chain) - 1 else f'{final[:-4]}_{k}.glb'
        if p.startswith('RAW '):
            lines.append('Q ' + p[4:].replace('{in}', cur).replace('{out}', out).replace('{start}', start) + ' | tail -2\n')
            cur = out
            continue
        tool = '$G $FS' if p.startswith('SMOOTH ') else '$G $F'
        args = p[len('SMOOTH '):] if p.startswith('SMOOTH ') else p
        lines.append(f'Q {tool} {cur} {out} {args} | tail -2\n')
        cur = out
    if not chain:
        lines.append(f'cp {start} {final}\n')
    return ''.join(lines)


def main():
    project, spec_path = Path(sys.argv[1]), Path(sys.argv[2])
    spec = json.loads(spec_path.read_text())
    notes = spec.get('notes', [])
    roles = {k: (v[0], v[1]) for k, v in spec['roles'].items()}
    roles_txt = '{\n' + ''.join(f'    {k!r}: ({v[0]!r}, {v[1]!r}),\n' for k, v in roles.items()) + '}'
    sfx = spec.get('suffix', '')
    (project / f'scripts/extra_clips_blend{sfx}.py').write_text(BLEND_TEMPLATE.format(
        blend=spec['blend'], notes='\n'.join(notes), roles=roles_txt, rig=spec.get('rig', 'MM9_Rig'),
        holds=spec.get('holds', {}), post_code='\n'.join(spec.get('post_code', [])),
        post_arg=', post=post' if spec.get('post_code') else '', hold_mode=spec.get('hold_mode', 'rec'),
        prep_code='\n'.join(spec.get('prep_code', [])), pre_export_code='\n'.join(spec.get('pre_export_code', [])),
        extra_args=(', prep=prep' if spec.get('prep_code') else '')
        + (', pre_export=pre_export' if spec.get('pre_export_code') else '')
        + (', post_first=True' if spec.get('post_first') else '')))
    renamed = spec.get('exported_as', {})
    everything = [renamed.get(r, r) for r in list(roles) + list(spec.get('holds', {}))]
    compare = ''.join(f'echo "control {c} vs {a}"; Q $G ../claude_shared/compare_clips.py work/gc.glb {c} $E {a} | tail -3\n'
                      for c, a in spec.get('controls', {}).items())
    sh = SH_TEMPLATE.format(
        blend=spec['blend'], notes=''.join(f'# {n}\n' for n in notes),
        graft_all=' '.join(f'--clip {c}' for c in everything),
        floor_ctl=passes(spec.get('floor_ctl', []), 'work/g0.glb', 'work/gc.glb') if spec.get('controls') else '',
        compare=compare,
        floor_new=passes(spec.get('floor_new', []), 'work/g0.glb', 'work/gn.glb'),
        graft_new=' '.join(f'--clip {c}' for c in spec['new']), sfx=sfx,
        name=spec.get('name', '$(basename "$here" | sed \'s/_claude$//\')'))
    path = project / f'scripts/extra_clips{sfx}.sh'
    path.write_text(sh)
    path.chmod(0o775)
    print('wrote', project / f'scripts/extra_clips_blend{sfx}.py', path)


if __name__ == '__main__':
    main()
