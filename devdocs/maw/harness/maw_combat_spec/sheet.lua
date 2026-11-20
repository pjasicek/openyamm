-- prints the sheet derivation for the example champion
local quiet = print
print = function() end
dofile("examples.lua")
print = quiet
for _,L in ipairs({50,150}) do
  Game.BolsterAmount=100
  vars.MMLVL={L,0,0,0}
  local p, info = champion(L)
  local sword=p.items[1]; local bow=p.items[2]
  local function rows(it)
    local wDmg,wDice,wFlat=GetWeaponDamage(it)
    local b,s=GetWeaponDamageRows(it)
    return wDmg,wDice,wFlat,b,s
  end
  print("L",L,"stat",info.S,"eff",Game.GetStatisticEffect(info.S),"skill est",estimateSkill(L),"wsk",info.wsk,"arms",info.am)
  print(" sword IL",MawCore.ItemLevel.OfItem(sword),"tierflat",GetWeaponFlatDamage(sword),"wDmg/wDice/wFlat/bonus/sides",rows(sword))
  print(" bow   IL",MawCore.ItemLevel.OfItem(bow),"wDmg/wDice/wFlat/bonus/sides",rows(bow))
  local t=plItemsStats[0]
  print(" rows 40..47",t[40],t[41],t[42],t[43],t[44],t[45],t[46],t[47]," AC row",t[10],"HP row",t[8],"res11",t[11])
  print(" recovery sword",getItemRecovery(sword,L),"bow",getItemRecovery(bow,L),"speed bonus",GetSpeedBonusFromStat(info.S))
  print(" HPtable", HPtable[2])
end
