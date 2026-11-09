"""Check native light/texture state in the scenario saves (assertions not exposed by scenario YAML).

Read only the bounded EventRuntimeState sprite/light maps defined in game/maps/SaveGame.cpp;
reject a changed layout instead of accepting an unchecked snapshot.
"""
import json
import shutil
import struct
from pathlib import Path

PROJECT=Path(__file__).resolve().parent
SAVES=Path('/tmp/openyamm_scenario_saves/hesper_d11_seedship_sabotage')
semantic=json.loads((PROJECT/'source/hes_d11.semantic.json').read_text())
sprite_ids={131,141,142}|{p['event'] for p in semantic['pickups'] if p['event']<750}

def state(path):
    data=path.read_bytes()
    marker=b'hes_kreegan_pod_chest'
    anchor=data.index(marker)
    candidates=[]
    for start in range(max(0,anchor-80*len(sprite_ids)),anchor):
        if data[start:start+8] != struct.pack('<Q',len(sprite_ids)):continue
        cursor=start+8;sprites={}
        try:
            for _ in sprite_ids:
                key,hidden,present=struct.unpack_from('<IBB',data,cursor);cursor+=6
                assert key in sprite_ids and hidden in (0,1) and present==1
                length=struct.unpack_from('<Q',data,cursor)[0];cursor+=8
                assert 0<length<64
                text=data[cursor:cursor+length].decode('ascii');cursor+=length
                sprites[key]=(hidden,text)
            count=struct.unpack_from('<Q',data,cursor)[0];cursor+=8
            assert set(sprites)==sprite_ids and 5<=count<=12
            lights={}
            for _ in range(count):
                key,on=struct.unpack_from('<IB',data,cursor);cursor+=5
                assert on in (0,1) and key<=22
                lights[key]=on
            candidates.append((sprites,lights))
        except (AssertionError,UnicodeDecodeError,struct.error):continue
    assert len(candidates)==1,(path,len(candidates))
    return data,*candidates[0]

results=[]
for k in range(1,5):
    data,sprites,lights=state(SAVES/f'd11_ganglion_{k}.oysav')
    # Compiler sorts the twelve BLV lights by source id: G1-G4 first, then L1-L8.
    assert [lights[i] for i in range(4)]==[0]*k+[1]*(4-k),(k,lights)
    if k==4:
        assert struct.pack('<IQ',155,8)+b'hsbraind' in data
        assert lights[8]==0
        assert all(sprites[i]==(0,'hes_d11_nerve_node_off') for i in (141,142))
    results.append(dict(after_ganglion=k,lights=lights,fixtures=sprites))
data,sprites,lights=state(SAVES/'d11_blind.oysav')
assert struct.pack('<IQ',155,8)+b'hsbraind' in data
assert all(lights[i]==0 for i in (0,1,2,3,8))
assert all(sprites[i]==(0,'hes_d11_nerve_node_off') for i in (141,142))
shutil.copy2(SAVES/'d11_blind.oysav',PROJECT/'review/hes_d11_blind.oysav')
results.append(dict(blind_tour_save='review/hes_d11_blind.oysav',lights=lights,fixtures=sprites))
# Same-map MoveToMap has no scenario transition trace. Check its native movement-state prefix.
arrival=struct.pack('<fffff',600,600,0,160,0)
assert arrival not in (SAVES/'d11_before_hatch.oysav').read_bytes()
assert arrival in (SAVES/'d11_after_hatch.oysav').read_bytes()
results.append(dict(hatch_arrival=[600,600,0],eye_height=160))
(PROJECT/'review/saved_state_checks.json').write_text(json.dumps(results,indent=2)+'\n')
print('PASS: ganglion lights, dead brain, nerve shutdown, aft-deck hatch arrival; verified blind tour save copied to review/')
