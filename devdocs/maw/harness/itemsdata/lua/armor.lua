dofile(arg[3])
local powers = {0, 5, 10, 20, 40, 60, 80, 100, 120}
local function inBands(i) return (i>=1 and i<=151) or (i>=803 and i<=936) or (i>=1603 and i<=1736) end
local hdr = "id\tname\tfamily\tslot\tskill\tbaseAC\trefAC"
for _, p in ipairs(powers) do hdr = hdr .. "\tP" .. p end
print(hdr)
local slotName = {[3]="armor",[4]="shield",[5]="helm",[6]="belt",[7]="cloak",[8]="gauntlets",[9]="boots"}
for i = 1, 1736 do
  local t = Game.ItemsTxt[i]
  if inBands(i) and t.EquipStat >= 3 and t.EquipStat <= 9 and ((t.Skill>=8 and t.Skill<=11) or t.Skill==40) then
    local ac = t.Mod1DiceCount + t.Mod2
    local row = {i, t.Name, t.NotIdentifiedName, slotName[t.EquipStat], t.Skill, ac, referenceAC[i]}
    for _, p in ipairs(powers) do
      local v = ac
      if p > 0 then v = ac + round(MawCore.Formulas.chargesArmorAC(referenceAC[i], p)) end
      row[#row+1] = v
    end
    print(table.concat(row, "\t"))
  end
end
