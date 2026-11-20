dofile(arg[1] .. "/shim.lua")
local S = "/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/"
loadChunk(S .. "General/zz_Maw-initialize.lua")
loadChunk(S .. "Modules/MawCore/Formulas.lua")
loadChunk(S .. "Modules/MawCore/ItemLevel.lua")
loadChunk(S .. "General/zMaw_ItemBits.lua")
loadChunk(S .. "General/zzMaw-Items.lua")
loadChunk(S .. "General/zzAlchemy.lua")
local function fmt(x) if x == math.floor(x) then return string.format("%d", x) end return string.format("%.2f", x) end

print("== Primordial max / gem caps per difficulty power ==")
local diffs = {
  {"Easy..Hell", function() vars = {} end},
  {"Nightmare(true)", function() vars = {trueNightmare = true} end},
  {"Doom", function() vars = {Mode = 2} end},
  {"Insanity/Madness", function() vars = {Mode = 2, insanityMode = true} end},
}
local groups = {{"x1 (1H,shield,belt,cloak,amulet)", 0}, {"x1.25 (bow,helm,gaunt,boots)", 2}, {"x1.5 body", 3},
  {"x2 2H", 1}, {"x0.75 ring", 10}}
for _, d in ipairs(diffs) do
  d[2]()
  print(string.format("-- %s: PrimordialMax=%s", d[1], fmt(GetPrimordialMaxEnchantStrength())))
  local hdr = "tier"
  for _, g in ipairs(groups) do hdr = hdr .. " | " .. g[1] end
  hdr = hdr .. " | skill x1 | skill x1.25 | skill x1.5 | skill x2 | skill x0.75"
  print(hdr)
  for tier = 1, 20 do
    local line = tostring(tier)
    for _, g in ipairs(groups) do line = line .. " | " .. fmt(GetGemCap(tier, g[2], false)) end
    for _, g in ipairs({0, 2, 3, 1, 10}) do line = line .. " | " .. fmt(GetGemCap(tier, g, true)) end
    print(line)
  end
end
vars = {}

print("== Crafting Cube cap by player level ==")
for _, lvl in ipairs({1, 20, 50, 100, 200, 300, 400, 500, 600, 1000}) do
  io.write(lvl, "->", fmt(GetCraftingCubeCap(lvl)), "  ")
end
print()

print("== gem tier distribution (MAW normal_random, 200000 samples) ==")
math.randomseed(12345)
for _, lvl in ipairs({10, 20, 50, 100, 200, 400, 600, 1000}) do
  local counts = {}
  local N = 200000
  for i = 1, N do
    local s = math.floor(normal_random(math.max(lvl^0.6/4+1, lvl/40), 2))
    s = math.max(math.min(s, GEM_DROP_MAX_TIER), 1)
    counts[s] = (counts[s] or 0) + 1
  end
  local mean = 0
  local parts = {}
  for t = 1, 16 do
    local c = counts[t] or 0
    mean = mean + t * c / N
    if c / N >= 0.005 then parts[#parts + 1] = string.format("T%d %.1f%%", t, 100 * c / N) end
  end
  print(string.format("L%d mu=%.2f meanTier=%.2f: %s", lvl, math.max(lvl^0.6/4+1, lvl/40), mean, table.concat(parts, ", ")))
end

print("== expected drops per 1000 kills (renewal rate with MAW pity_chance) ==")
local function rate(base, b)
  if b <= 0 then return 0 end
  local inc = round(b)
  local survive, expected, c = 1, 0, 0
  for k = 0, 5e7 do
    expected = expected + survive
    local p = math.min(1, pity_chance(base, c) * b)
    survive = survive * (1 - p)
    if survive < 1e-12 then break end
    c = c + inc
  end
  return 1000 / expected
end
local names = {[1061]="Eye", [1062]="Hourglass", [1063]="Pandora", [1064]="Mirror", [1065]="Emerald", [1066]="Pearl",
  [1067]="Oracle", [1068]="CelestialOrb", [1070]="CraftCube"}
local order = {1061, 1062, 1063, 1064, 1065, 1066, 1067, 1068, 1070}
for _, kind in ipairs({{"regular", 1}, {"boss x10", 10}, {"no-corpse x3", 3}}) do
  print("-- " .. kind[1])
  local hdr = "level | b | gems(normal) | gems(insanity x1.5)"
  for _, id in ipairs(order) do hdr = hdr .. " | " .. names[id] end
  print(hdr)
  for _, lvl in ipairs({20, 50, 100, 200, 400}) do
    local b = (lvl / 10)^0.5 * kind[2]
    local line = string.format("%d | %.2f | %.2f | %.2f", lvl, b, 1000 * math.min(1, 0.006 * b), 1000 * math.min(1, 0.006 * b * 1.5))
    for _, id in ipairs(order) do line = line .. string.format(" | %.4g", rate(craftDropChances[id], b)) end
    print(line)
  end
end
print("-- nominal (no pity) per 1000 at b=1: ")
for _, id in ipairs(order) do io.write(names[id], "=", craftDropChances[id] * 1000, " ") end
print()
print("-- pity: chance right after reset vs base, and counter units to certainty")
for _, id in ipairs(order) do
  local base = craftDropChances[id]
  print(string.format("%s base=%.3g reset=%.3g (%.0f%% of base) certain at %.0f units", names[id], base,
    pity_chance(base, 0), 100 * pity_chance(base, 0) / base, 2.76 / base))
end

print("== shop special-item chance per qualifying stock slot ==")
for _, gold in ipairs({10000, 100000, 1e6, 5e6, 1e7, 2e7}) do
  io.write(string.format("%g: %.2f%%  ", gold, 100 * math.min((gold / 20000000)^0.7, 1)))
end
print()

print("== map completion gem tier ==")
for _, L in ipairs({1, 5, 10, 20, 30, 40, 50, 60, 80, 100}) do
  local free = math.min(math.ceil((L + 0) / 25 + 0.5), GEM_DROP_MAX_TIER)
  local hor = math.min(math.ceil((L + 2 * L) / 25 + 0.5), GEM_DROP_MAX_TIER)
  io.write(string.format("L%d free=T%d horizontal=T%d; ", L, free, hor))
end
print()
