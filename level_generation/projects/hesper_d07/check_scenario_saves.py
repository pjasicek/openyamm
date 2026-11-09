"""Check native actor visibility and one-shot mine damage, which the scenario YAML cannot directly compare."""
import json
import struct
import re
from pathlib import Path

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
SAVES=Path('/tmp/openyamm_scenario_saves')
actors=json.loads((PROJECT/'source/hes_d07.semantic.json').read_text())['actors']

def saved(scenario,name):return SAVES/('hesper_d07_'+scenario)/('d07_'+name+'.oysav')

def visibility(scenario,name,groups):
    raw=saved(scenario,name).read_bytes()
    # shortcut: inspect the version-100 MapDeltaActor prefix; update this check when SaveGame.cpp changes it.
    assert raw[:8]==b'OYSAVE1\0' and struct.unpack_from('<I',raw,8)[0]==100
    for group,hidden in groups.items():
        wanted=[a for a in actors if a['group']==group]
        found=[]
        for label,mid in {(a['name'],a['monster']) for a in wanted}:
            text=label.encode();needle=struct.pack('<Q',len(text))+text
            start=0
            while (start:=raw.find(needle,start))>=0:
                offset=start+len(needle);start+=1
                # Validate the surrounding native fields before treating a matching string as an actor record.
                if struct.unpack_from('<h',raw,offset)[0]!=0:continue
                if struct.unpack_from('<hh',raw,offset+11)!=(mid,mid):continue
                if struct.unpack_from('<I',raw,offset+49)[0]!=group:continue
                attributes=struct.unpack_from('<I',raw,offset+2)[0]
                found.append(bool(attributes&0x10000))
        # A save contains scene and runtime copies: every copy must agree, not just the first match.
        assert found and len(found)%len(wanted)==0,(scenario,name,group,len(found))
        assert all(flag==hidden for flag in found),(scenario,name,group,found,hidden)
    print('PASS visibility',scenario,name,groups)

visibility('main_path','line_stopped',{12:True,13:True})
visibility('main_path','line_stopped_after_41',{12:True,13:True})
visibility('main_path','quiet_free',{8:False,9:True})
visibility('loud_path','coupled',{8:True,9:False})
visibility('loud_path','loud_free',{8:False,9:True})
visibility('loud_path','alarm_waves',{5:False,6:False})
visibility('factory_and_mines','gm_free',{8:False,9:True,5:True,6:True})
visibility('factory_and_mines','line_first',{12:False,13:True})
visibility('factory_and_mines','line_second',{12:False,13:False})

log=(ROOT/'output/hesper_stage/logs/d07_factory_and_mines.log').read_text()
health=[list(map(int,re.findall(r'(\d+)/\d+',line))) for line in log.splitlines() if line.startswith('PARTY_HEALTH ')]
assert health==[[5040]*5,[4965]*5,[4965]*5],health
print('PASS: native mine damage is exactly 75 once per member, including after save/load')
