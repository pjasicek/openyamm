"""Focused Lua checks for D9's persistent null field, one-shot waves and bounded hatchlings."""
import ctypes
from pathlib import Path

project = Path(__file__).resolve().parent
lua = ctypes.CDLL('liblua5.4.so.0')
lua.luaL_newstate.restype = ctypes.c_void_p
for name, args, result in (
    ('luaL_openlibs', [ctypes.c_void_p], None),
    ('luaL_loadstring', [ctypes.c_void_p, ctypes.c_char_p], ctypes.c_int),
    ('lua_pcallk', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ssize_t, ctypes.c_void_p], ctypes.c_int),
    ('lua_tolstring', [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p], ctypes.c_char_p),
    ('lua_close', [ctypes.c_void_p], None),
):
    function = getattr(lua, name)
    function.argtypes, function.restype = args, result

mock = '''
local vars, bits, doors, hidden, notes = {}, {}, {}, {}, {}
local sp, maximum, player = {7, 123, 0, 4097}, {7, 123, 20, 4097}, 1
local metadata, events = {}, {}
HesperPickups={setup=function(c) assert(#c.vats==8 and #c.bundles==20) end}
MonsterBits={Invisible=65536}; FacetBits={Invisible=1,Untouchable=2}
VarTag={CurrentSpellPoints=5}; PartySelector={Current=7,All=5}
Damage={Body=8}
function SetMapMetadata(m) metadata=m end
function QBit(v) return v end
function MapVar(v) return v end
function IsQBitSet(v) return bits[v] end
function SetQBit(v) bits[v]=true end
function ClearQBit(v) bits[v]=nil end
function SetAutonote(v) notes[v]=true end
function IsAtLeast(v,n) return (vars[v] or 0)>=n end
function SetValue(v,n) vars[v]=n end
function RegisterEvent(id,title,fn) events[id]=fn end
local chest, splash, status
local noop=function() end
evt={GetPartyMemberCount=function() return #sp end,
    ForPlayer=function(p) if p<4 then player=p+1 end end,
    Cmp=function(_,n) return sp[player]>=n end,
    Set=function(_,n) sp[player]=math.min(n,maximum[player]) end,
    GetMapVar=function(k) return vars[k] or 0 end,
    SetMapVar=function(k,v) vars[k]=v end,
    SetDoorState=function(k,v) doors[k]=v end,
    SetMonGroupBit=function(k,_,v) hidden[k]=v end,
    OpenChest=function(k) chest=k end,
    GetPartyPosition=function() return 6600,3300,0 end,
    DamagePlayer=function(_,kind,amount) splash={kind,amount} end,
    CheckMonstersKilled=function() return false end,
    SetFacetBit=noop,SetActorBehavior=noop,SetLight=noop,StatusText=function(s) status=s end,SimpleMessage=noop}
'''
handlers = (project / 'source/hes_d09.handlers.lua').read_text().replace('D9_ACTORS, ', '').replace('D9_EXIT, ', '')
checks = '''
handlers[50](); assert(status=='The membrane mouth: the way is not yet open.')
handlers[1]()
assert(vars.sp1==7 and vars.sp2==123 and vars.sp3==0 and vars.sp4==4097)
for _,v in ipairs(sp) do assert(v==0) end
handlers[1]() -- save/load inside must not replace saved SP with zero
assert(vars.sp2==123)
sp[2]=50; handlers[3](); assert(sp[2]==0)
maximum[4]=2000; handlers[5]()
assert(sp[1]==7 and sp[2]==123 and sp[3]==0 and sp[4]==2000 and vars.null_on==0)
sp[1]=3; handlers[1](); handlers[5](); assert(sp[1]==3)
handlers[30](); assert(chest==nil)
handlers[71](); handlers[30](); assert(chest==0 and vars[3]==1)
handlers[70](); assert(splash[1]==Damage.Body and splash[2]>=2 and splash[2]<=12)
handlers[152](); assert(vars.wave1==1 and hidden[28]==0 and doors[66]==0)
hidden[28]=9; handlers[152](); assert(hidden[28]==9)
handlers[151](); assert(bits[100011] and not bits[100211] and doors[51]==0 and notes[10232])
handlers[31](); assert(chest==1)
handlers[1](); assert(hidden[24]==1 and hidden[30]==1)
Behavior={define=function(t) return t end}
'''
cluster = (project / 'source/hes_egg_cluster.lua').read_text()
checks += '\nlocal behavior=(function()\n' + cluster + '\nend)()\n' + '''
local timer, distance, summoned = false, 3000, 0
local actor={hasTimer=function() return timer end,
    startTimer=function(_,name,seconds) assert(seconds==15); timer=true end,
    distanceToParty=function() return distance end,
    summon=function(_,id,count) assert(id==10003 and count==1); summoned=summoned+1 end}
local state={}
behavior.onStart(actor,state)
local function tick() assert(timer); timer=false; behavior.onTimer.hatch(actor,state) end
tick(); assert(summoned==0 and timer)
distance=2000; tick(); assert(summoned==1 and timer)
behavior.onLoad(actor,state); tick(); assert(summoned==2 and not timer)
behavior.onLoad(actor,state); assert(not timer and state.hatched==2)
'''
state = lua.luaL_newstate()
lua.luaL_openlibs(state)
try:
    status = lua.luaL_loadstring(state, (mock + handlers + checks).encode())
    if not status:
        status = lua.lua_pcallk(state, 0, 0, 0, 0, None)
    assert status == 0, lua.lua_tolstring(state, -1, None).decode()
finally:
    lua.lua_close(state)
print('PASS: exit fallback, per-member SP capture/restore/clamp, reentry, vat gate, waves, completion, two-hatchling cap')
