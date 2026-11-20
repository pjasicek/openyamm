dofile(arg[1] .. "/shim.lua")
local S = "/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/"
loadChunk(S .. "General/zz_Maw-initialize.lua")
loadChunk(S .. "Modules/MawCore/Formulas.lua")
loadChunk(S .. "General/zMaw_ItemBits.lua")
loadChunk(S .. "General/zzMaw-Items.lua")
loadChunk(S .. "General/zzAlchemy.lua")
vars = {}
-- Cheapest single-enchant plan: always use the lowest tier whose cap is above the current strength.
local function plan(equipStat, from, skill)
  local s, used, cost16 = from, {}, 0
  local step = skill and GEM_STEP_SKILL or GEM_STEP
  while true do
    local t
    for tier = 1, 20 do if GetGemCap(tier, equipStat, skill) > s then t = tier break end end
    if not t then break end
    s = math.min(s + step, GetGemCap(t, equipStat, skill))
    used[t] = (used[t] or 0) + 1
    if t > 16 then cost16 = cost16 + 3^(t - 16) else cost16 = cost16 + 1 end
  end
  local n, parts = 0, {}
  for t = 1, 20 do if used[t] then n = n + used[t]; parts[#parts+1] = "T" .. t .. "x" .. used[t] end end
  return s, n, cost16, table.concat(parts, " ")
end
for _, c in ipairs({{"1H x1", 0}, {"2H x2", 1}, {"body x1.5", 3}, {"helm x1.25", 5}, {"ring x0.75", 10}}) do
  local s, n, cost, parts = plan(c[2], 0, false)
  local s2, n2, cost2 = plan(c[2], GetGemCap(16, c[2], false), false)
  print(string.format("%s: 0->%d uses %d gems (%s); tiers 17-20 only (from T16 cap %d): %d gems = %d tier-16 gems",
    c[1], s, n, parts, GetGemCap(16, c[2], false), n2, cost2))
end
local s, n, cost, parts = plan(0, 0, true)
print(string.format("skill 1H: 0->%d uses %d gems (%s)", s, n, parts))
