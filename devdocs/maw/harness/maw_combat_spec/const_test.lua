offsets={MMVersion=8, PatchDll={}}
internal={MMVersion=8}
mem={dll=setmetatable({},{__index=function() return {} end}), i4={}}
AppPath=""
function table.invert(t) local r={} for k,v in pairs(t) do r[v]=k end return r end
function table.copy(s,d) d=d or {} for k,v in pairs(s) do d[k]=v end return d end
local ok,err=pcall(dofile,"/home/pjasicek/github/OpenYAMM/reference/mmmerge/Scripts/Core/ConstAndBits.lua")
print(ok,err)
print(const.Skills.Bow, const.Skills.Learning, const.Damage.Energy, const.Spells.Fireball, const.MonsterBuff.DamageHalved, const.Race and const.Race.Dragon, const.Class and const.Class.Thief, const.AIState and const.AIState.Dead, const.MonsterKind and const.MonsterKind.Dragon)
