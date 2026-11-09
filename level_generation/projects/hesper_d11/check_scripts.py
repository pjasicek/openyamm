"""Focused Lua checks for duel selection, saved door timers, rewards and bounded summons."""
import ctypes
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
lua = ctypes.CDLL('liblua5.4.so.0')
lua.luaL_newstate.restype = ctypes.c_void_p
for name, args, result in (
    ('luaL_openlibs', [ctypes.c_void_p], None),
    ('luaL_loadstring', [ctypes.c_void_p, ctypes.c_char_p], ctypes.c_int),
    ('lua_pcallk', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                    ctypes.c_ssize_t, ctypes.c_void_p], ctypes.c_int),
    ('lua_tolstring', [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p], ctypes.c_char_p),
    ('lua_close', [ctypes.c_void_p], None),
):
    function = getattr(lua, name)
    function.argtypes, function.restype = args, result

mock = '''
local vars, bits, attached, doors, items, hidden = {}, {}, {}, {}, {}, {}
local gold, summons, prompt, damage = 0, 0, false, {}
local noop = function() end
MonsterBits = {Invisible=65536}; Damage = {Body=8}; VarTag = {Gold=10}
QBit=function(v) return v end; MapVar=QBit
IsQBitSet=function(v) return bits[v] end
SetQBit=function(v) bits[v]=true end
ClearQBit=function(v) bits[v]=nil end
SetValue=function(k,v) vars[k]=v end
IsAtLeast=function(k,v) return (vars[k] or 0)>=v end
AddValue=function(k,v) assert(k==VarTag.Gold); gold=gold+v end
SetAutonote=noop; SetMapMetadata=noop; RegisterMapTimerEvent=noop
HesperPickups={setup=noop}
AskChoiceWithAnswerSteps=function() prompt=true end
evt={SetActorBehavior=function(i,b) attached[i]=b end,
    GetMapVar=function(k) return vars[k] or 0 end,
    SetMapVar=function(k,v) vars[k]=v end,
    SetDoorState=function(k,v) doors[k]=v end,
    SetMonGroupBit=function(k,_,v) hidden[k]=v end,
    GiveItem=function(id) items[id]=(items[id] or 0)+1 end,
    CheckMonstersKilled=function() return false end,
    GetPartyPosition=function() return 1800,4500,0 end,
    GetPartyMemberCount=function() return 2 end,
    PartyMemberHasEquippedItem=function(p,id) return p==1 and id==11106 end,
    DamagePlayer=function(p,kind,n) assert(kind==Damage.Body); damage[p]=(damage[p] or 0)+n end,
    SetTexture=noop,SetSprite=noop,SetLight=noop,PlaySoundName=noop,
    StatusText=noop,SimpleMessage=noop,OpenChest=noop,MoveToMap=noop}
'''
handlers = (PROJECT / 'source/hes_d11.handlers.lua').read_text()
handlers = handlers.replace('D11_ACTORS, ',
    '{index=22,group=6,behavior="hes_ganglion"}, '
    '{index=79,group=25,behavior="hes_vhorrax_honour"}, '
    '{index=80,group=26,behavior="hes_vhorrax_refused"}, ')
handlers = handlers.replace('D11_EXIT, ', '')
checks = '''
handlers[1]()
assert(attached[22] and not attached[79] and not attached[80])
handlers[160](0); assert(prompt)
handlers[160](3); assert(not bits[100029] and not bits[100030])
handlers[160](1)
assert(bits[100029] and not bits[100030] and attached[79] and not attached[80])
handlers[160](2); assert(not attached[80])
handlers[1](); assert(attached[79] and not attached[80])
for _=1,3 do handlers[3]() end
assert(damage[0]>=8 and damage[0]<=48 and not damage[1])
handlers[201](); assert(vars.d11_close_201==10)
handlers[1]() -- Reload retains the pending close countdown in map state.
for _=1,10 do handlers[3]() end
assert(doors[201]==1 and vars.d11_close_201==0)
handlers[30](); handlers[31](); assert(next(items)==nil)
handlers[156](); handlers[30](); handlers[31]()
assert(items[11421]==1 and items[11331]==2 and items[11377]==1)
assert(items[11480]==1 and items[11332]==1 and items[11482]==1 and gold==50000)
handlers[1](); handlers[30](); handlers[31](); assert(items[11331]==2 and gold==50000)
vars,bits,attached,items,gold = {},{[100030]=true},{},{},0
handlers[1](); assert(attached[80] and not attached[79])
handlers[156](); handlers[30](); handlers[31]()
assert(not items[11421] and items[11332]==2 and items[11331]==2 and gold==0)
Behavior={define=function(v) return v end}
local actor={setNoFlee=noop,hasTimer=function() return false end,startTimer=noop,
    perform=noop,castNext=noop,say=noop,effect=noop,
    summon=function(_,id,count,radius) summons=summons+count end}
'''
boss = (PROJECT / 'source/hes_vhorrax.lua').read_text()
for honour in ('true', 'false'):
    checks += '\nlocal boss=(function()\n' + boss.replace('HONOUR', honour) + '\nend)()\n'
    if honour == 'false':
        checks += '''
local s={}; summons=0; boss.onStart(actor,s)
for _=1,8 do boss.onTimer.adds(actor,s) end
boss.onLoad(actor,s); boss.onTimer.adds(actor,s)
assert(summons==4 and s.adds==4)
'''
ganglion = (PROJECT / 'source/hes_ganglion.lua').read_text()
checks += '\nlocal ganglion=(function()\n' + ganglion + '\nend)()\n'
checks += 'summons=0; ganglion.onDeath(actor,{}); assert(summons==4)\n'
state = lua.luaL_newstate()
lua.luaL_openlibs(state)
try:
    status = lua.luaL_loadstring(state, (mock + handlers + checks).encode())
    if not status:
        status = lua.lua_pcallk(state, 0, 0, 0, 0, None)
    assert status == 0, lua.lua_tolstring(state, -1, None).decode()
finally:
    lua.lua_close(state)
print('PASS: chosen boss only, sealed helm, saved door countdown, one-shot rewards, four-add cap, ganglion hatchlings')
