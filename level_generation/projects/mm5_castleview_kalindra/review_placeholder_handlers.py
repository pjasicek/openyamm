"""Execute every authored Lua placeholder with only the permitted status-text API."""
import hashlib
import json
from pathlib import Path
import subprocess

PROJECT = Path(__file__).resolve().parent

LUA_REVIEW = r'''
local events, messages = {}, {}
local environment = {
    SetMapMetadata = function(metadata)
        for key, value in pairs(metadata) do
            assert(key == "onLoad" and type(value) == "table" and next(value) == nil,
                   "Unexpected map lifecycle behavior")
        end
    end,
    RegisterEvent = function(id, label, handler)
        assert(type(id) == "number" and type(label) == "string" and type(handler) == "function")
        assert(events[id] == nil, "Duplicate event ID")
        events[id] = {label = label, handler = handler}
    end,
    evt = {StatusText = function(message) messages[#messages + 1] = message end}
}
setmetatable(environment, {
    __index = function(_, key) error("Unexpected global API: " .. key) end,
    __newindex = function(_, key) error("Unexpected global write: " .. key) end
})
assert(loadfile(arg[1], "t", environment))()
local ids = {}
for id in pairs(events) do ids[#ids + 1] = id end
table.sort(ids)
for _, id in ipairs(ids) do
    messages = {}
    events[id].handler()
    assert(#messages == 1, "Handler must issue exactly one status message")
    assert(messages[1] == events[id].label .. ": not implemented yet.", "Incorrect placeholder feedback")
    print(id)
end
'''


def review():
    script = PROJECT/'implementation/runtime/worlds/mm5/events/maps/mm5_sw.lua'
    result = subprocess.run(['lua', '-', str(script)], input=LUA_REVIEW, text=True,
                            capture_output=True, check=True)
    ids = [int(line) for line in result.stdout.splitlines()]
    semantic = json.loads((PROJECT/'implementation/source/mm5_sw.semantic.json').read_text())
    scenery = json.loads((PROJECT/'implementation/scenery.json').read_text())
    expected = sorted(event['id'] for event in semantic['events']+scenery['events'])
    assert ids == expected, 'Lua registrations differ from the current source binding inventory'
    report = {'status':'All authored placeholders executed successfully in restricted Lua.',
              'luaSha256':hashlib.sha256(script.read_bytes()).hexdigest(), 'eventIds':ids,
              'handlers':len(ids), 'permittedEffect':'Exactly one matching named status message per invocation.',
              'lifecycle':'Empty onLoad metadata; no other lifecycle behavior accepted.',
              'limits':'Handler smoke only. Native binding/readback, real picking, intrinsic descriptor overrides, '
                       'runtime population and save-state stability require their separate engine evidence.'}
    folder = PROJECT/'review/placeholder_handlers'
    folder.mkdir(exist_ok=True)
    (folder/'smoke.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Executed all {len(ids)} authored status-only Lua handlers.')


if __name__=='__main__':
    review()
