local quiet=print; print=function() end
dofile("examples.lua")
print=quiet
for _,L in ipairs({50,150}) do
  Game.BolsterAmount=100
  vars.MMLVL={L,0,0,0}
  local p=champion(L)
  p.items[1].Bonus2=12
  vars.mawbuff[4]=true
  buffSkills[4]={20,4,L}
  local mon=makeMonster(L,{[0]=50,[1]=0,[2]=0,[3]=0,[4]=10,[6]=0,[7]=0,[8]=0,[9]=0,[10]=20})
  local it=p.items[1]
  local lo,hi,avg=enchantDamageRange(it,12)
  print(string.format("L%d weaponLevelDamage %.4f enchant12 range %.4f-%.4f avg %.4f baseRecovery %.1f itemRecovery %d aura raw %.4f",
    L, GetWeaponLevelDamage(it), lo, hi, avg, GetPlayerBaseRecovery(p,it), getItemRecovery(it,L), GetWeaponLevelDamage(it)*0.25))
  RNG_U=0.999
  CURRENT_HIT={Player=p}
  mapvars={}
  local t={DamageKind=4,Damage=10,Result=10,Player=p,PlayerIndex=0,MonsterIndex=0,Monster=mon}
  for _,r in ipairs(tracePipe(MawCore.Damage.pipe,t)) do print(r) end
  print("  elemental part", t.ElementalDamage, "final", t.Result)
  vars.mawbuff[4]=nil
end
