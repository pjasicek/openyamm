dofile(arg[3])
local powers = {0, 5, 10, 20, 30, 40, 60, 80, 100, 120}
local function inBands(i) return (i>=1 and i<=151) or (i>=803 and i<=936) or (i>=1603 and i<=1736) end
local ancient = {[866]=true,[867]=true,[1666]=true,[1667]=true}
local out = {}
local hdr = "id\tname\tfamily\tskill\t2H\tladder\tdice"
for _, p in ipairs(powers) do hdr = hdr .. "\tP" .. p end
hdr = hdr .. "\tspd0\tspd250\tspd500\tspd600"
print(hdr)
for i = 1, 1736 do
  local t = Game.ItemsTxt[i]
  if inBands(i) and not ancient[i] and t.EquipStat <= 2 then
    local row = {i, t.Name, t.NotIdentifiedName, t.Skill, IsTwoHandedWeapon(makeItem(i,0)) and 1 or 0,
      string.format("%.2f", MawCore.ItemLevel.LadderTier(i)), t.Mod1DiceCount}
    for _, p in ipairs(powers) do
      local bonus, lo, hi = GetWeaponDamageMinMax(makeItem(i, p))
      row[#row+1] = string.format("+%d %d-%d", bonus, lo, hi)
    end
    for _, p in ipairs{0, 50, 100, 120} do row[#row+1] = getItemRecovery(makeItem(i, p), 0)/100 end
    print(table.concat(row, "\t"))
  end
end
