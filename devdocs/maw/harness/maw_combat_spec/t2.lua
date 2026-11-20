dofile("chars.lua")
for _,L in ipairs({50,150}) do
  vars.MMLVL={L,0,0,0}
  local S=round(estimateStat(L))
  local sk=estimateSkill(L)
  local wsk=round(sk*1.5)
  local m=masteryForSkill(wsk)
  local am=round(sk); local amm=masteryForSkill(am)
  local p=makePlayer{Class=19, Level=L, Stat=S, Skills={
    [const.Skills.Sword]={wsk,m},[const.Skills.Bow]={wsk,m},[const.Skills.Armsmaster]={am,amm},
    [const.Skills.Chain]={am,amm},[const.Skills.Bodybuilding]={am,math.min(amm,3)}},
    Items={[1]=makeItem(101, MawCore.ItemLevel.PowerFor(L)), [2]=makeItem(102, MawCore.ItemLevel.PowerFor(L)), [3]=makeItem(103, MawCore.ItemLevel.PowerFor(L))}}
  pl=p
  local t=installParty(p)
  print("L",L,"S",S,"wsk",wsk,m,"arms",am,amm)
  print(" melee",p:GetMeleeDamageMin(),p:GetMeleeDamageMax(),"atk",p:GetMeleeAttack(),"delay",p:GetAttackDelay(false), damageMultiplier[0].Melee)
  print(" ranged",p:GetRangedDamageMin(),p:GetRangedDamageMax(),"atk",p:GetRangedAttack(),"delay",p:GetAttackDelay(true), damageMultiplier[0].Ranged)
  print(" AC",p:GetArmorClass(),"res",p:GetResistance(10),"HP",p:GetFullHP())
  print(" model AC",EST.estimateArmorClass(L),"res",EST.estimateResistance(L),"HP",EST.estimateHealth(L),"atk",getPlayerEstimatedAttack(L))
end
