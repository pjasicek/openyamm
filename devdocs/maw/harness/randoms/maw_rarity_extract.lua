const=const or {}
const.Rarity={
	Common=1,
	Uncommon=2,
	Rare=3,
	Epic=4,
	Ancient=5,
	Primordial=6,
	Legendary=7,
	Celestial=8,
}

rarityUpgradeChance = {
	[const.Rarity.Celestial]  = 0.002,
	[const.Rarity.Legendary]  = 0.03,
	[const.Rarity.Primordial] = 0.04,
	[const.Rarity.Ancient]    = 0.12,
}

shopRarityRedirect = {
	[const.Rarity.Celestial]  = false,
	[const.Rarity.Legendary]  = false,
	[const.Rarity.Primordial] = false,
	[const.Rarity.Ancient]    = const.Rarity.Primordial,
}
--the AncientTier a Primordial carries, which is what a shop Ancient gets charged as
SHOP_ANCIENT_PRICE_TIER = 2

BOSS_ROLL_DIVISOR = 4	--band roll window: math.random()/BOSS_ROLL_DIVISOR
BOSS_RARITY_MULT = 2	--upgrade cascade multiplier

local rarityDifficultyMult = {
	[1] = 1,	--bolster 40
	[2] = 1,	--bolster 70
	[3] = 1,	--bolster 100, baseline
	[4] = 1.1,	--bolster 150
	[5] = 1.2,	--bolster 200
	[6] = 1.4,	--bolster 300
	[7] = 1.6,	--doom
	[8] = 1.8,	--road to insanity
	[9] = 2,	--beyond madness
}

local rarityPityField = {
	[const.Rarity.Celestial]  = "celestialPityCounter",
	[const.Rarity.Legendary]  = "legendaryPityCounter",
	[const.Rarity.Primordial] = "primordialPityCounter",
}

--rows must stay ordered: Epic <= Rare <= Uncommon <= Common, or the band in
--between collapses to nothing
enchantChances={
	[const.Rarity.Epic]    ={Base=5,   PerTier=0.75, Cap=20},
	[const.Rarity.Rare]    ={Base=20,   PerTier=2,   Cap=60},
	[const.Rarity.Uncommon]={Base=60,  PerTier=1,  Cap=80},
	[const.Rarity.Common]  ={Base=100, PerTier=0,   Cap=100},
}
--all three bands reach their Cap at tier 20
function GetEnchantChance(rarity, lootTier)
	local c=enchantChances[rarity]
	return math.min(c.Base + c.PerTier*lootTier, c.Cap)
end

function GetEnchantBands(lootTier, difficulty)
	local mult=rarityBandMult[difficulty or GetDifficulty()] or {}
	local widths, total, previous = {}, 0, 0
	for r=const.Rarity.Epic, const.Rarity.Common, -1 do
		local threshold=GetEnchantChance(r, lootTier)
		local w=math.max(threshold-previous, 0)*(mult[r] or 1)
		widths[r]=w
		total=total+w
		previous=threshold
	end
	if total<=0 then
		return {[const.Rarity.Common]=100}, 100
	end
	for r, w in pairs(widths) do
		widths[r]=w/total*100
	end
	return widths, 100
end

rarityBandMult={
	[1]={},	--bolster 40
	[2]={},	--bolster 70
	[3]={},	--bolster 100, baseline
	[4]={[const.Rarity.Epic]=1.5, [const.Rarity.Rare]=1.4, [const.Rarity.Uncommon]=1.4},	--bolster 150
	[5]={[const.Rarity.Epic]=2,   [const.Rarity.Rare]=1.8, [const.Rarity.Uncommon]=1.6},	--bolster 200
	[6]={[const.Rarity.Epic]=2.5, [const.Rarity.Rare]=2.2, [const.Rarity.Uncommon]=1.8},	--bolster 300
	[7]={[const.Rarity.Epic]=3,   [const.Rarity.Rare]=2.6, [const.Rarity.Uncommon]=2},	--doom
	[8]={[const.Rarity.Epic]=4,   [const.Rarity.Rare]=3, [const.Rarity.Uncommon]=2.2},	--road to insanity
	[9]={[const.Rarity.Epic]=5.5, [const.Rarity.Rare]=3.4, [const.Rarity.Uncommon]=2.4},	--beyond madness
}

enchantStrengthRange={
	[const.Rarity.Celestial] ={Min=25, Max=25},
	[const.Rarity.Primordial]={Min=25, Max=25},
	[const.Rarity.Ancient]   ={Min=20, Max=25},
	[const.Rarity.Legendary] ={Min=16, Max=20},
}
ENCHANT_STRENGTH_DEFAULT={Min=8, Max=20}	--Common..Epic
ENCHANT_STRENGTH_DIV=20

enchantCountByRarity={
	[const.Rarity.Common]=0,
	[const.Rarity.Uncommon]=1,
	[const.Rarity.Rare]=2,
	[const.Rarity.Epic]=3,
	[const.Rarity.Ancient]=3,
	[const.Rarity.Primordial]=3,
	[const.Rarity.Legendary]=3,
	[const.Rarity.Celestial]=3,
}

--The rarity an item IS, as opposed to the one it was rolled at. Nothing
--stores it: RollItemRarity only decides it while generating, so it has to be
--read back off the item -- the rarity bits for everything from ancient up,
--the enchant count (the same one enchantCountByRarity states) below that.
function MawItemRarity(it)
	if IsCelestialItem(it) then
		return const.Rarity.Celestial
	elseif HasLegendaryAffix(it) then
		return const.Rarity.Legendary
	end
	local tier=GetAncientTier(it)
	if tier==2 then
		return const.Rarity.Primordial
	elseif tier==1 then
		return const.Rarity.Ancient
	end
	local enchants=0
	if it.Bonus>0 then enchants=enchants+1 end
	if HasEnc2(it) then enchants=enchants+1 end
	if it.Bonus2>0 then enchants=enchants+1 end
	if enchants>=enchantCountByRarity[const.Rarity.Epic] then
		return const.Rarity.Epic
	elseif enchants>=enchantCountByRarity[const.Rarity.Rare] then
		return const.Rarity.Rare
	elseif enchants>=enchantCountByRarity[const.Rarity.Uncommon] then
		return const.Rarity.Uncommon
	end
	return const.Rarity.Common
end

cubeQualityStep={
	[const.Rarity.Common]=20,
	[const.Rarity.Uncommon]=20,
	[const.Rarity.Rare]=10,
	[const.Rarity.Epic]=7,
	[const.Rarity.Ancient]=5,
	[const.Rarity.Primordial]=4,
	[const.Rarity.Legendary]=4,
	[const.Rarity.Celestial]=1,
}
CUBE_QUALITY_STEP_ARTIFACT=2

function CanTakeCube(it)
	local txt=it:T()
	if txt.EquipStat<=2 and txt.Skill<const.Skills.Shield then
		return true
	end
	return (txt.Skill>=const.Skills.Shield and txt.Skill<=const.Skills.Plate)
		or (txt.Skill==40 and txt.EquipStat~=12)
end

function GetCubeQualityStep(it)
	if not CanTakeCube(it) then
		return 0
	end
	if IsArtifactItem(it) then
		return CUBE_QUALITY_STEP_ARTIFACT
	end
	return cubeQualityStep[MawItemRarity(it)] or 0
end

function MawQualityText(it)
	local quality=GetItemQuality(it)
	if quality<=0 then
		return ""
	end
	return StrColor(255, 190, 90, "\nQuality bonus: +" .. quality .. "%")
end
--============================= end RARITY =============================

function GetRarityBaseMultiplier(lootTier, lootMultiplier, difficulty)
	--how far the loot has ramped at this tier, from the same curve the roll uses
	local tierFactor=GetEnchantChance(const.Rarity.Uncommon, lootTier)
		/enchantChances[const.Rarity.Uncommon].Cap
	return (rarityDifficultyMult[difficulty or GetDifficulty()] or 1)
		*tierFactor*(lootMultiplier or 1)^0.5
end

function GetRarityMultiplier(lootTier, bossLoot, lootMultiplier)
	local mult=GetRarityBaseMultiplier(lootTier, lootMultiplier)
	if bossLoot then
		mult=mult*BOSS_RARITY_MULT
	end
	if mapvars and mapvars.mapAffixes then
		local nAff=0
		for i=1,4 do
			if mapvars.mapAffixes[i]>0 then
				nAff=nAff+1
			end
		end
		mult=mult*(1+(mapvars.mapAffixes.Power*nAff+nAff*20)/400)
	end
	return mult
end

function RollItemRarity(lootTier, bossLoot, noLegendary, lootMultiplier, isShop)
	local mult=GetRarityMultiplier(lootTier, bossLoot, lootMultiplier)
	local result=const.Rarity.Epic
	for rarity=const.Rarity.Celestial, const.Rarity.Ancient, -1 do
		local base=rarityUpgradeChance[rarity]
		if isShop then
			local borrow=shopRarityRedirect[rarity]
			base=borrow and rarityUpgradeChance[borrow] or 0
		elseif noLegendary and rarity>=const.Rarity.Legendary then
			base=0
		end
		if base>0 then
			local field=rarityPityField[rarity]
			local chance=base
			if field then
				vars[field]=vars[field] or 0
				chance=pity_chance(base, vars[field])
			end
			chance=chance*mult
			if math.random()<chance then
				if field then
					vars[field]=0
				end
				result=rarity
				break
			end
		end
	end
	--a rarity this roll could never have produced does not charge its pity, which
	--is what the noLegendary case already did -- the shop just blocks more of them
	for rarity, field in pairs(rarityPityField) do
		local blocked=(isShop and not shopRarityRedirect[rarity])
			or (noLegendary and rarity>=const.Rarity.Legendary)
		if rarity>result and not blocked then
			vars[field]=(vars[field] or 0)+mult
		end
	end
	return result
end

local function enchantStrengthMean(rarity)
	local range=enchantStrengthRange[rarity] or ENCHANT_STRENGTH_DEFAULT
	return (range.Min+range.Max)/2/ENCHANT_STRENGTH_DIV
end

--one drop's worth, as a fraction of that ceiling: how many enchant slots the
--rarity fills, times how hard they rolled
local function rarityItemFraction(rarity)
	local slots=enchantCountByRarity[const.Rarity.Celestial]
	local ceiling=enchantStrengthMean(const.Rarity.Primordial)
	return enchantCountByRarity[rarity]/slots*enchantStrengthMean(rarity)/ceiling
end

function GetRarityDistribution(lootTier, difficulty)
	local bands=GetEnchantBands(lootTier, difficulty)
	local dist={}
	for rarity=const.Rarity.Common, const.Rarity.Epic do
		dist[rarity]=(bands[rarity] or 0)/100
	end
	local epic=dist[const.Rarity.Epic]
	local mult=GetRarityBaseMultiplier(lootTier, nil, difficulty)
	local left=1
	for rarity=const.Rarity.Celestial, const.Rarity.Ancient, -1 do
		local chance=math.min(rarityUpgradeChance[rarity]*mult, 1)
		dist[rarity]=epic*left*chance
		left=left-left*chance
	end
	dist[const.Rarity.Epic]=epic*left
	return dist
end

--Each failure raises the chance; the exponent is picked so that the AVERAGE
--wait stays at 1/chance (within 2% for every rate in use, from 0.5% to 12%).
--At 1.45 the curve started so far under the nominal chance that it cost ~10%
--more rolls than having no pity at all.
local PITY_EXPONENT = 1.38
function pity_chance(chance, failures)
	--above 1 the exponent would turn the curve upside down and LOWER it
	if chance>=1 then
		return 1
	end
	return chance^(PITY_EXPONENT-chance*failures*0.5)
end
function get_affix(counts)
    local v = {}
    local total = 0
	local N=#counts
    -- Calculate the weight for each affix
    for i = 1, N do
        v[i] = 1 / (N * (counts[i] + 1))
        total = total + v[i]
    end

    -- Compute cumulative probabilities
    local cumulative = {}
    local cum_sum = 0
    for i = 1, N do
        cum_sum = cum_sum + v[i] / total
        cumulative[i] = cum_sum
    end

    -- Generate a random number between 0 and 1
    local r = math.random()

    -- Find and return the affix corresponding to the random number
    for i = 1, N do
        if r <= cumulative[i] then
            return i
        end
    end

    -- Fallback in case of rounding errors
    return N
end
