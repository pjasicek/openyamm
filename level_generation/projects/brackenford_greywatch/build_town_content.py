"""Create scoped Brackenford house/NPC instances from current merged MM8 records.

Original tables and generated legacy Lua remain untouched. Installation appends these rows to an isolated base.
Teacher topics retain the existing mastery rules; ambient topics are restricted to audited message-only handlers.
"""
import csv
import hashlib
import json
from pathlib import Path
import re

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[2]
TABLES=ROOT/'assets_dev/engine/data_tables'
IDS=json.loads((PROJECT/'source/ids.json').read_text())


def read(name):
    with (TABLES/name).open(encoding='cp1252',newline='') as stream:
        return {int(row[0]):row for row in csv.reader(stream,delimiter='\t') if row and row[0].isdigit()}


houses=read('house_data.txt');animations=read('house_animations.txt');npcs=read('npc.txt')
topics=read('npc_topic.txt');teachers=read('teacher_topics.txt')
semantics=json.loads((PROJECT/'source/lg01.semantic.json').read_text())
profiles={'stables':452,'weapon_shop':2,'armor_shop':37,'magic_shop':77,'tavern':229,
          'temple':304,'training':1568,'alchemist':111,'civic_hall':773}
residents={
    'civic_hall':(245,[664]),
    'teacher_1':(113,[304]), 'teacher_2':(149,[343]),
    'teacher_3':(182,[394]), 'teacher_4':(185,[388]),
    'resident_1':(247,[661]), 'resident_2':(248,[662,671]), 'resident_3':(249,[663,662]),
    'resident_4':(253,[666]), 'resident_5':(254,[655]), 'resident_6':(315,[718]),
    'warehouse_1':(242,[671]), 'warehouse_2':(230,[674]),
    'well_lane_cottage':(217,[676]), 'court_west_long':(218,[679]),
    'court_west_small':(219,[675]), 'court_south_long':(243,[669]), 'court_east_small':(244,[670]),
    'residence_7':(221,[677]), 'residence_8':(220,[678]), 'residence_9':(319,[722]),
}
assert len({v[0] for v in residents.values()})==len(residents)
global_lua=(ROOT/'assets_dev/engine/events/Global.lua').read_text(encoding='cp1252')
global_handlers={int(m[1]):m[0] for m in re.finditer(
    r'RegisterGlobalEvent\((\d+),.*?(?=\nRegisterGlobalEvent|\Z)',global_lua,re.S)}
deltas={'house_data.txt':[],'house_animations.txt':[],'npc.txt':[]}
inventory=[]
for index,building in enumerate(semantics['buildings']):
    key=building['id'];house_id=IDS['house_base']+index
    assert house_id not in houses and house_id not in animations
    original_npc_id,selected_topics=residents.get(key,(None,[]))
    profile=profiles.get(key)
    if profile is None:
        profile=int(npcs[original_npc_id][6])
    house=list(houses[profile]);animation=list(animations[profile])
    house[0]=str(house_id);house[3]=str(IDS['maps']['lg01.odm'])
    # These are local virtual interiors. No inherited extra-exit or global quest restriction is meaningful here.
    house[20:24]=['0','0','0','0']
    if house[6]=='Placeholder':house[6]=''
    animation[0]=str(house_id);animation[3]=''
    record={'id':'mm8:brackenford:house:'+key,'building':key,'house_id':house_id,
        'event_id':building['event_id'],'source_house_id':profile,'source_house_name':houses[profile][5],
        'house_name':house[5],'service_type':house[2],'service_rule_id':int(house[1]),
        'proprietor':house[6],'portrait':house[8],'video':animation[4],
        'door_position':building['door_position'],'door_outward':building['door_outward'],
        'approach_yaw':building['approach_yaw'],'building_form':building['form'],'npc':None}
    if key=='civic_hall':
        house[5]="Myles Greydawn - Guildmaster's Residence";animation[2]=house[5];record['house_name']=house[5]
    if original_npc_id is not None:
        original=npcs[original_npc_id];npc_id=IDS['npc_base']+len(deltas['npc.txt'])
        assert npc_id not in npcs
        original_topics=[int(v) for v in original[10:16] if v.isdigit() and int(v)]
        assert set(selected_topics)<=set(original_topics)
        copied=list(original);copied[0]=str(npc_id);copied[6]=str(house_id)
        copied[10:16]=[str(t) for t in selected_topics]+['0']*(6-len(selected_topics))
        copied[16]='Brackenford instance of MM8 NPC '+str(original_npc_id)+'; original unchanged'
        animation[3]=str(npc_id)
        deltas['npc.txt'].append(copied)
        topic_records=[]
        for topic_id in selected_topics:
            topic=topics[topic_id]
            if topic_id in teachers:
                behavior={'kind':'mastery_teacher','rule':teachers[topic_id]}
            else:
                handler=global_handlers[topic_id]
                # Strip quoted strings before auditing executable tokens. No quest/state/award branches are allowed.
                code=re.sub(r'"(?:\\.|[^"\\])*"','""',handler)
                assert re.fullmatch(r'RegisterGlobalEvent\(\d+, "", function\(\)\s*'
                                    r'evt\.SetMessage\(""\)\s*end\)\s*',code), (key,topic_id,code)
                behavior={'kind':'existing_message_only_global_handler',
                    'source':'assets_dev/engine/events/Global.lua',
                    'sha256':hashlib.sha256(handler.encode('cp1252')).hexdigest()}
            topic_records.append({'id':topic_id,'title':topic[1],'text_reference':topic[4],'behavior':behavior})
        record['npc']={'canonical_id':'mm8:brackenford:npc:'+str(original_npc_id),
            'instance_id':npc_id,'source_id':original_npc_id,'name':copied[1],
            'portrait':int(copied[2]),'greeting':int(copied[8]),'topics':topic_records,
            'omitted_source_topics':sorted(set(original_topics)-set(selected_topics))}
    deltas['house_data.txt'].append(house);deltas['house_animations.txt'].append(animation)
    inventory.append(record)
assert len(inventory)==IDS['house_count'] and len(deltas['npc.txt'])==IDS['npc_count']
assert len({r['behavior']['rule'][2] for h in inventory if h['npc'] for r in h['npc']['topics']
            if r['behavior']['kind']=='mastery_teacher'})==4
result={'format_version':1,'map':'lg01.odm','canonical_map':'mm8:brackenford',
    'house_id_range':[IDS['house_base'],IDS['house_base']+len(inventory)-1],
    'npc_id_range':[IDS['npc_base'],IDS['npc_base']+len(deltas['npc.txt'])-1],
    'rows':deltas,'houses':inventory,
    'source_tables':{name:hashlib.sha256((TABLES/name).read_bytes()).hexdigest()
                     for name in ['house_data.txt','house_animations.txt','npc.txt','npc_topic.txt','teacher_topics.txt']},
    'notes':[
      'Stock/training/tavern/transport rules are immutable shared MM8 profiles; inventory state uses new house IDs.',
      'Training uses MM8 Assassin\'s School / Lehava (house1568, cap200), so the level25 party can progress here.',
      'No legacy teacher-autonote NPC alias is copied; runtime notes should record the actual Brackenford position.',
      'Stable schedule reuses MM8 Guild Caravans routes; regional returns remain a separate required integration.',
      'Ambient selected topics are existing message-only handlers; omitted topics include quests and misplaced geography.']}
(PROJECT/'source/town_registry.json').write_text(json.dumps(result,indent=2)+'\n')
lua='-- Generated local house IDs; edit build_town_content.py/source inventory, never legacy scripts.\n'
lua+='LG.houses = {\n'+''.join(f'    [{h["event_id"]}] = {h["house_id"]}, -- {h["house_name"]}\n' for h in inventory)+'}\n'
(PROJECT/'source/lg01.town.lua').write_text(lua)
lines=['# Brackenford MM8 town reuse inventory','',
       'New numeric IDs own local house/NPC state. Original NPCs, dialogue text and service rules remain unchanged.','',
       '| Building | House instance / source | MM8 proprietor or resident | Topics / service |',
       '| --- | --- | --- | --- |']
for h in inventory:
    npc=h['npc'];person=npc['name']+f' (NPC {npc["instance_id"]} ← {npc["source_id"]})' if npc else h['proprietor']
    descriptions=', '.join(str(t['id'])+': '+t['title'] for t in npc['topics']) if npc else h['service_type']
    lines.append(f'| {h["building"]} | {h["house_id"]} ← {h["source_house_id"]} | {person} | {descriptions} |')
lines+=['','The JSON inventory records exact portrait, greeting, topic, video and source-table provenance.',
        'Four teachers cover Master Sword, Master Water Magic, Master Disarm Trap and Master Perception.',
        'The civic hall uses the MM8 Merchant Guildhouse presentation and Myles Greydawn’s existing Ogres and Bandits topic.',
        'Content-only placement revisions use quick native binding/registry checks and visual review. Re-run focused runtime checks when behavior changes.']
(PROJECT/'TOWN_REUSE.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'houses':len(inventory),'npcs':len(deltas['npc.txt']),'teachers':4,'ambient_residents':len(deltas['npc.txt'])-4}))
