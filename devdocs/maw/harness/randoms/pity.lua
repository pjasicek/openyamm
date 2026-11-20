dofile(HERE.."harness.lua")
-- renewal statistics: hazard h(k) = min(pity_chance(base, k*inc) * mult, 1)
local function stats(base, inc, mult)
  if inc == 0 then local h=pity_chance(base,0)*mult return 1/h, nil, {} end
  local S, E, k, q = 1, 0, 0, {}
  local cert
  while S > 1e-13 do
    E = E + S
    local h = math.min(pity_chance(base, k*inc)*mult, 1)
    local Sn = S*(1-h)
    for _,p in ipairs{0.5,0.9,0.99} do if not q[p] and Sn <= 1-p then q[p]=k+1 end end
    S = Sn; k = k+1
  end
  cert = math.ceil(2.76/base/inc - 1e-9)
  return E, cert, q
end
local function geo(p) local function qq(x) return math.ceil(math.log(1-x)/math.log(1-p)) end return 1/p, qq(0.5), qq(0.9), qq(0.99) end
local rows = {
  {"Celestial upgrade (celestialPityCounter)", 0.002},
  {"Legendary upgrade (legendaryPityCounter)", 0.03},
  {"Primordial upgrade (primordialPityCounter)", 0.04},
  {"Artifact substitution (artifactRollPity)", 0.005},
  {"Eye of Void 1061", 0.0002}, {"Hourglass 1062", 0.0002}, {"Pandora 1063", 0.001}, {"Mirror 1064", 0.00001},
  {"Emerald 1065", 0.00025}, {"Pearl 1066", 0.0002}, {"Oracle Orb 1067", 0.00006}, {"Celestial Orb 1068", 0.0000025},
  {"Crafting Cube 1070", 0.001},
  {"Broodlord boss (insanity x3)", 0.03}, {"Omnipotent boss (insanity x3)", 0.003},
  {"Map drop, all dungeons done (pre-level factor)", 0.001},
}
print("name | base | chance at counter 0 (ratio) | counter for certainty | E[wait] (x 1/base) | median/p90/p99 pity | median/p90/p99 no pity")
for _,r in ipairs(rows) do
  local base=r[2]
  local E, cert, q = stats(base, 1, 1)
  local gE, g50, g90, g99 = geo(base)
  print(string.format("%s | %g | %.4g%% (%.3f) | %d | %.1f (%.3f) | %d/%d/%d | %d/%d/%d",
    r[1], base, pity_chance(base,0)*100, pity_chance(base,0)/base, cert, E, E*base, q[0.5], q[0.9], q[0.99], g50, g90, g99))
end
print()
print("chance after N failures (counter = N, mult 1), % :")
local Ns={0,1,5,10,25,50,100,200,500,1000,2000,5000,10000,20000,50000,100000,200000,500000,1000000}
for _,r in ipairs(rows) do
  local s=r[1].." :"
  for _,n in ipairs(Ns) do
    local c=math.min(pity_chance(r[2], n),1)
    if n*r[2] <= 3 then s=s..string.format(" N=%d:%.4g", n, c*100) end
  end
  print(s)
end
print()
print("rarity upgrades with multiplier m (counter += m, chance x m), E[wait] in Epic-band rolls:")
for _,base in ipairs{0.002,0.03,0.04} do
  local s=string.format("base %g:", base)
  for _,m in ipairs{0.75,1,1.5,2,2.4,3,4} do local E=stats(base,m,m); s=s..string.format(" m=%.2f:%.1f(1/(base*m)=%.1f)", m, E, 1/(base*m)) end
  print(s)
end
print()
print("crafting specials per kill: chance x b, counter += round(b); E[kills] for b = bonusRoll")
for _,r in ipairs(rows) do if r[1]:match("^%u%l+ ?%u?%l* ?%d") or r[1]:match("10%d%d") then
  local s=r[1]..":"
  for _,b in ipairs{0.45, 1, 3.16, 10, 31.6} do
    local E=stats(r[2], math.floor(b+0.5), b); s=s..string.format(" b=%.2f:%.4g kills (flat %.4g)", b, E, 1/(r[2]*b))
  end
  print(s)
end end
