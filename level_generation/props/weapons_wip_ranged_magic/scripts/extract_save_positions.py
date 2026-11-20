"""Read the settled owned-item positions from the version-88 all-items review save, without changing it.

The console layout contains launch positions: thrown items settle farther south and lower down.
Only the known version-88 WorldItemState/InventoryItem record layout is accepted here.
"""
import hashlib
import json
import math
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
save = ROOT / 'saves/Ground items test.oysav'
data = save.read_bytes()
assert data[:8] == b'OYSAVE1\0' and struct.unpack_from('<I', data, 8)[0] == 88
owned = json.loads((HERE / 'ownership.json').read_text())
positions = {}
for row in owned:
    item_id = row['items'][0]['id']
    offset = -1
    matches = set()
    while (offset := data.find(struct.pack('<I', item_id), offset + 1)) >= 0:
        if offset < 4 or struct.unpack_from('<I', data, offset + 4)[0] != 1:
            continue
        if not 0 < struct.unpack_from('<I', data, offset - 4)[0] < 5000:
            continue
        # 32-byte InventoryItem, gold amount/bool, eight uint16 fields and int16 sector.
        cursor = offset + 32 + 5 + 18
        valid = True
        try:
            for _ in range(2):
                size = struct.unpack_from('<Q', data, cursor)[0]
                cursor += 8
                if not 1 <= size <= 100:
                    valid = False
                    break
                name = data[cursor:cursor + size].decode('ascii')
                valid = valid and all(32 <= ord(c) <= 126 for c in name)
                cursor += size
            if not valid:
                continue
            values = struct.unpack_from('<9f', data, cursor)
            if all(math.isfinite(v) and abs(v) < 32768 for v in values) and values[3:6] == (0, 0, 0):
                matches.add(values[:3])
        except (UnicodeError, struct.error):
            continue
    # The save repeats snapshots; repeated records must agree on one actual resting position.
    assert len(matches) == 1, (row['icon'], matches)
    positions[row['icon']] = list(matches.pop())
assert len(positions) == 56
(HERE / 'receipts/settled_positions.json').write_text(json.dumps({
    'save': str(save.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'version': 88,
    'positions': positions}, indent=2) + '\n')
print('Read 56 unique resting positions; repeated snapshots agree; source save unchanged')
