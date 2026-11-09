"""Assemble generated data/registrations around preserved authored outdoor Lua handlers."""
import json
from pathlib import Path

PROJECT=Path(__file__).resolve().parent


def assemble():
    source=PROJECT/'source'
    semantics=json.loads((source/'lg01.semantic.json').read_text())
    town=json.loads((source/'town_registry.json').read_text())
    house_titles={h['event_id']:h['house_name'] for h in town['houses']}
    text='-- Generated assembly; edit source/lg01.handlers.lua and the town inventory.\nlocal LG = {}\n'
    text+=(source/'lg01.town.lua').read_text()+'\n'
    text+='SetMapMetadata({onLoad={},onLeave={},openedChestIds={[201]={0},[202]={1},[203]={2},[204]={3}},contextActions={\n'
    text+='    [301]={kind="obelisk",source="authored"}, [302]={kind="well",source="authored"}, [303]={kind="well",source="authored"}, [304]={kind="fountain",source="authored"},\n'
    for house in town['houses']:
        text+=f'    [{house["event_id"]}] = {{kind="enter_house",source="authored",houseId={house["house_id"]},'
        text+=f'targetName={json.dumps(house["house_name"])}}},\n'
    text+='}})\n'
    text+=(source/'lg01.handlers.lua').read_text()+'\n'
    for event in semantics['events']:
        event_id=event['id']
        special={201:'Chest',202:'Chest',203:'Chest',204:'Chest',301:'Obelisk',302:'Drink from the well',303:'Drink from the well',304:'Drink from the fountain'}
        title=special.get(event_id,house_titles.get(event_id,event['name'].replace('_',' ').capitalize()))
        text+=f'assert(type(handlers[{event_id}]) == "function", "Missing Brackenford handler {event_id}")\n'
        text+=f'RegisterEvent({event_id},{json.dumps(title)},handlers[{event_id}],{json.dumps(title)})\n'
    (PROJECT/'runtime/worlds/mm8/events/maps/lg01.lua').write_text(text)
    print(f'Assembled Brackenford Lua: {len(semantics["events"])} events, {len(house_titles)} house instances')


if __name__=='__main__':
    assemble()
