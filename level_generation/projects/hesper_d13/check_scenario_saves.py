"""Check actual native hidden-group flags and the vent arrival, which scenario YAML cannot directly compare."""
import json
import struct
from pathlib import Path

P=Path(__file__).resolve().parent
actors=json.loads((P/'runtime/hes_d13.scene.yml').read_text())['initial_state']['actors']


def saved(scenario,name):
    raw=(Path('/tmp/openyamm_scenario_saves')/('hesper_d13_'+scenario)/(name+'.oysav')).read_bytes()
    # shortcut: versions 106/133 have the checked actor/movement prefixes; recheck after serializer changes.
    assert raw[:8]==b'OYSAVE1\0' and struct.unpack_from('<I',raw,8)[0] in (106,133)
    return raw


def visibility(raw,groups):
    for group,hidden in groups.items():
        wanted=[a for a in actors if a['group']==group];found=[]
        for label,mid in {(a['name'],a['monster_id']) for a in wanted}:
            text=label.encode();needle=struct.pack('<Q',len(text))+text;start=0
            while (start:=raw.find(needle,start))>=0:
                offset=start+len(needle);start+=1
                if struct.unpack_from('<h',raw,offset)[0]!=0:continue
                if struct.unpack_from('<hh',raw,offset+11)!=(mid,mid):continue
                if struct.unpack_from('<I',raw,offset+49)[0]!=group:continue
                found.append(bool(struct.unpack_from('<I',raw,offset+2)[0]&0x10000))
        assert found and len(found)%len(wanted)==0,(group,len(found))
        assert all(flag==hidden for flag in found),(group,found,hidden)


visibility(saved('d13_override','d13_override_first'),{5:False,6:True,7:True,8:True})
visibility(saved('d13_override','d13_override_second'),{5:False,6:False,7:True,8:True})
visibility(saved('d13_collapse_reset','d13_collapse_shown'),{7:False,8:False})
raw=saved('d13_collapse_reset','d13_after_vent')
visibility(raw,{7:True,8:True})
# IndoorMoveState's exact position, eye height and stopped vertical velocity, followed by valid sector ids.
needle=struct.pack('<fffff',5228,1000,0,160,0);start=0;found=[]
while (start:=raw.find(needle,start))>=0:
    sector,eye_sector=struct.unpack_from('<hh',raw,start+20)
    if 0<sector<=14 and 0<eye_sector<=14:found.append(start)
    start+=1
assert found,'The native vent save contains no party movement state at tap_ring'
print('PASS: native wave flags, hidden collapse groups, and vent party position [5228,1000,0]')
