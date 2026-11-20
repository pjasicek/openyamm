dofile(HERE.."harness.lua")
local R=const.Rarity
local names={"Common","Uncommon","Rare","Epic","Ancient","Primordial","Legendary","Celestial"}
local diffNames={"Easy","Normal","MAW","Hard","Hell","Nightmare","Doom","RoadToInsanity","BeyondMadness"}
local bolster={40,70,100,150,200,300,"doom","insanity","madness"}

-- expected number of Epic-band trials until success, hazard h(k)=min(pity(base,k*m)*m,1)
function expectedWait(base, m)
  local S, E, k = 1, 0, 0
  while S > 1e-15 do
    E = E + S
    local h = math.min(pity_chance(base, k*m)*m, 1)
    S = S*(1-h); k = k+1
    if k > 1e7 then break end
  end
  return E
end

-- band shares for Common..Epic; boss divides the uniform roll by BOSS_ROLL_DIVISOR
function bandShares(tier, d, boss)
  local bands = GetEnchantBands(tier, d)
  local window = boss and 100/BOSS_ROLL_DIVISOR or 100
  local out, cum, prev = {}, 0, 0
  for r=R.Epic, R.Common, -1 do
    cum = cum + (bands[r] or 0)
    local hi = math.min(cum, window)
    out[r] = (hi - math.min(prev, window))/window
    prev = cum
  end
  return out
end

-- cascade given Epic share; mode "nominal" (GetRarityDistribution) or "pity" (long-run renewal)
function cascade(epic, mult, mode)
  local f = {}
  if mode == "nominal" then
    local left = 1
    for r=R.Celestial, R.Ancient, -1 do
      local c = math.min(rarityUpgradeChance[r]*mult, 1)
      f[r] = left*c; left = left - left*c
    end
    f[R.Epic] = left
  else
    local fc = 1/expectedWait(rarityUpgradeChance[R.Celestial], mult)
    local fl = (1-fc)/expectedWait(rarityUpgradeChance[R.Legendary], mult)
    local fp = (1-fc-fl)/expectedWait(rarityUpgradeChance[R.Primordial], mult)
    local fa = (1-fc-fl-fp)*math.min(rarityUpgradeChance[R.Ancient]*mult, 1)
    f[R.Celestial], f[R.Legendary], f[R.Primordial], f[R.Ancient] = fc, fl, fp, fa
    f[R.Epic] = 1-fc-fl-fp-fa
  end
  for r=R.Epic, R.Celestial do f[r] = f[r]*epic end
  return f
end

function distribution(tier, d, boss, mode)
  local b = bandShares(tier, d, boss)
  local mult = GetRarityBaseMultiplier(tier, nil, d) * (boss and BOSS_RARITY_MULT or 1)
  local f = cascade(b[R.Epic], mult, mode)
  local out = {}
  for r=R.Common, R.Rare do out[r] = b[r] end
  for r=R.Epic, R.Celestial do out[r] = f[r] end
  return out, mult
end
