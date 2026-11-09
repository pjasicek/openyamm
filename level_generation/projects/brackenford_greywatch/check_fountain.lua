-- Focused authored-handler check; no engine launch or repeated service scenarios.
local root = arg[1] or 'level_generation/projects/brackenford_greywatch'
local state, now, hp, sp, message = {}, 1439, 0, 0, ''
local environment = setmetatable({LG={houses={}}, CurrentHealth='health', CurrentSpellPoints='mana'}, {__index=_G})
environment.CurrentGameMinutes = function() return now end
environment.AddValue = function(selector, amount)
    if selector=='health' then hp=hp+amount elseif selector=='mana' then sp=sp+amount else error(selector) end
end
environment.evt = {
    GetMapVar=function(key, default) if state[key]==nil then return default end return state[key] end,
    SetMapVar=function(key, value) state[key]=value end,
    StatusText=function(text) message=text end,
}
local source=assert(io.open(root..'/source/lg01.handlers.lua')):read('*a')
local function load_handler()
    return assert(load(source..'\nreturn handlers[304]', 'fountain', 't', environment))()
end
local drink=load_handler()
for i=1,40 do drink() end
assert(hp==600 and sp==600 and state['Brackenford.Fountain.Uses']==40)
drink();assert(hp==600 and sp==600 and message:find('tomorrow'))
-- Recreating the Lua map module must preserve exhaustion through saved named map state.
drink=load_handler();drink();assert(hp==600 and sp==600)
now=1440;drink();assert(hp==615 and sp==615 and state['Brackenford.Fountain.Uses']==1)
now=1440*400;drink();assert(hp==630 and sp==630 and state['Brackenford.Fountain.Uses']==1)
print('PASS: 40 shared uses, 41st blocked, module reload preserves depletion, midnight and long absence reset supply')
