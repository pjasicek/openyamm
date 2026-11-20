local quiet=print; print=function() end
dofile("chars.lua")
print=quiet
for _,b in ipairs({100,200}) do
  Game.BolsterAmount=b
  print(string.format("bolster %d diff %d", b, GetDifficulty()))
  print("L | estSkill | estStat | geared | maxEnchStr | health | AC | res | physTaken | magicTaken | toHit | vitality | power | attack | monHP(B) | monDmg(B)")
  for _,L in ipairs({1,10,50,100,150,200,300}) do
    local v,phys,mag,taken,health=getPlayerEstimatedVitality(L)
    print(string.format("%d | %.4f | %.4f | %.4f | %.4f | %.2f | %.2f | %.2f | %.4f | %.4f | %.4f | %.2f | %.4f | %.4f | %.2f | %.4f",
      L, estimateSkill(L), estimateStat(L), gearedFraction(L), GetMaxEnchantStrength(L), health, EST.estimateArmorClass(L), EST.estimateResistance(L),
      phys, mag, EST.estimateChanceToGetHit(L), v, getPlayerEstimatedPower(L), getPlayerEstimatedAttack(L), getMonsterHealth(nil,L), getMonsterDamage(nil,L)))
  end
end
