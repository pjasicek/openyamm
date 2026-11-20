dofile("harness.lua")
for _,L in ipairs({1,50,100,150,250}) do
  print(L, estimateSkill(L), estimateStat(L), getPlayerEstimatedPower(L), getPlayerEstimatedVitality(L), getPlayerEstimatedAttack(L), getMonsterHealth(nil,L), getMonsterDamage(nil,L))
end
