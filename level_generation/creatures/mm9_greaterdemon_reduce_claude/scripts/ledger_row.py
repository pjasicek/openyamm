#!/usr/bin/env python3
"""Replace the Greater Demon's row (59) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits
only the line starting with '| 59 | 1 monster | Greater Demon |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 59 | 1 monster | Greater Demon | `mm9_greaterdemon.glb` | 9,988 | 8,418 (-15.7 %; candidate j85: body 5,136 -> 4,270, '
       'membrane 1,648 -> 944, heads 3,204 byte-identical) | 4,158 / 1,378 / 369 (installed 4,945 / 1,665 / 460) | ready for '
       'review (fix pass, chart guard, UV audit 0) 2026-11-04 (greaterdemon-reduce-fix-20261104): h85 rolled back for 3 membrane '
       'faces off the charts, all re-emitted lining faces where the two shell sheets use opposite quad diagonals; fix: chart '
       'guard (MP_CHART=1, also on the lining twins), those 3 outer faces frozen and their quads re-emitted from the original '
       'lining faces, LOD protected points snapped (12/12); reduction_uv_audit LOD0 0 escaping in every primitive, LOD1-3 at the '
       'source LODs\' baseline; ladder j r85 p99 11.42 / max 32.0 mm (limits 11.55 / 57.75), IoU .995, SSIM .992; skin 0.85, '
       'wing bones 0.55, membrane 0.5, head primitive, spikes, wing root/body line, spike roots kept; gates as h85: edge '
       'min/max no worse, lowest point per clip identical, wing attachment 4.24 = 4.24 cm, detached 12 = 12 (Xaelbowpiv spike '
       '9.6 mm in Spawn only), winding/bone 0, LOD bounds kept, LOD3 floor -0.56 cm (installed -0.36); escape-site, head and body '
       'close-ups read: h85 wedges gone, heads identical; candidate export/mm9_greaterdemon.glb (sha256 3ae0fcadcb0b); not '
       'installed | `mm9_greaterdemon_reduce_claude/` | `mm9_greaterdemon_reduce_claude/before/mm9_greaterdemon.glb` (sha256 32d3d7a6a229) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 59 | 1 monster | Greater Demon |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 59 updated')
