-- Builds example characters and runs MAW's real itemStats() on them.
dofile("harness.lua")

-- expose Estimates.lua locals (formulas unchanged; only an accessor appended)
do
	local lines = {}
	for line in io.lines(MAW .. "Modules/MawCore/Estimates.lua") do lines[#lines + 1] = (line:gsub("\r$", "")) end
	local src = table.concat(lines, "\n") .. [[

EST = {estimateArmorClass = estimateArmorClass, estimateResistance = estimateResistance,
	estimateHealth = estimateHealth, estimateMana = estimateMana,
	estimateEnchantResistance = estimateEnchantResistance,
	estimateChanceToGetHit = estimateChanceToGetHit, coverMultiplier = coverMultiplier,
	estimateLegendaryDamageTaken = estimateLegendaryDamageTaken,
	estimatePhysicalDamageTaken = estimatePhysicalDamageTaken,
	estimateMagicDamageTaken = estimateMagicDamageTaken}
]]
	assert(load(src, "@Estimates.lua"))()
end

-- itemStats and its helpers (zzMaw-Items.lua:2555-3486 verbatim)
HasLegendaryAffix = function() return false end
GetLegendaryAffix = function() return 0 end
HasEnc2 = function() return false end
GetEnc2 = function() return 0, 0 end
updateCelestialItem = function() end
GetArmsmasterSupremeRequirement = function() return 100000 end
IsArtifactId = function() return false end
bonusEffects = {}
DAY_OF_PROTECTION_SKILL_PENALTY = 1.4

artifactLeech = {}
loadRange("General/zzMaw-Items.lua", 2555, 3486)
IsArtifactItem = function() return false end
IsArtifactWeapon = function() return false end
referenceAC = {}
referenceWeaponAttack = {}

-- ------------------------------------------------------------- item stubs
local ItemMT = {__index = {T = function(self) return Game.ItemsTxt[self.Number] end}}
function makeItem(number, maxCharges, bonus2)
	return setmetatable({Number = number, MaxCharges = maxCharges or 0, Bonus = 0, BonusStrength = 0,
		Bonus2 = bonus2 or 0, Broken = false, Charges = 0}, ItemMT)
end
-- synthetic item types (one per family -> LadderTier = ExpectedTier 3.5)
Game.ItemsTxt[101] = {Skill = const.Skills.Sword, EquipStat = 1, Mod1DiceCount = 3, Mod1DiceSides = 8, Mod2 = 0,
	NotIdentifiedName = "TwoHandedSword"}
Game.ItemsTxt[102] = {Skill = const.Skills.Bow, EquipStat = 2, Mod1DiceCount = 5, Mod1DiceSides = 2, Mod2 = 0,
	NotIdentifiedName = "Longbow"}
Game.ItemsTxt[103] = {Skill = const.Skills.Chain, EquipStat = 3, Mod1DiceCount = 0, Mod1DiceSides = 0, Mod2 = 30,
	NotIdentifiedName = "ChainMail"}
Game.ItemsTxt[104] = {Skill = const.Skills.Staff, EquipStat = 1, Mod1DiceCount = 2, Mod1DiceSides = 6, Mod2 = 0,
	NotIdentifiedName = "Staff"}
for i = 0, 2500 do
	if not Game.ItemsTxt[i] then
		Game.ItemsTxt[i] = {Skill = 40, EquipStat = 12, Mod1DiceCount = 0, Mod1DiceSides = 0, Mod2 = 0,
			NotIdentifiedName = "x" .. i}
	end
end
referenceWeaponAttack[101], referenceWeaponAttack[102], referenceWeaponAttack[104] = 0, 0, 0
referenceAC[103] = 30
Game.Classes.HPBase[19], Game.Classes.HPFactor[19] = 35, 8	-- Champion (MAW Class HP SP.txt)
Game.Classes.SPBase[19], Game.Classes.SPFactor[19] = 0, 0
Game.Classes.HPBase[46], Game.Classes.HPFactor[46] = 25, 3	-- ArchMage
Game.Classes.SPBase[46], Game.Classes.SPFactor[46] = 15, 6

-- ------------------------------------------------------------- player stub
local PlayerMT = {}
PlayerMT.__index = PlayerMT
local function eff(v) return Game.GetStatisticEffect(v) end
function PlayerMT:GetIndex() return self.index end
function PlayerMT:stat(n) return self[n .. "Base"] + self[n .. "Bonus"] + trunc((plItemsStats[self.index] or {})[self.statIx[n]] or 0) end
function PlayerMT:GetMight() return self:stat("Might") end
function PlayerMT:GetIntellect() return self:stat("Intellect") end
function PlayerMT:GetPersonality() return self:stat("Personality") end
function PlayerMT:GetEndurance() return self:stat("Endurance") end
function PlayerMT:GetAccuracy() return self:stat("Accuracy") end
function PlayerMT:GetSpeed() return self:stat("Speed") end
function PlayerMT:GetLuck() return self:stat("Luck") end
function PlayerMT:GetSkill(id) return self.Skills[id] or 0 end
function PlayerMT:GetActiveItem(slot) return self.items[slot] end
function PlayerMT:EnumActiveItems()
	local k = -1
	return function()
		while k < 15 do
			k = k + 1
			if self.items[k] then return self.items[k] end
		end
	end
end
-- the engine receives CalcStatBonusByItems results as C ints: truncate toward zero
function trunc(x) if x >= 0 then return math.floor(x) end return -math.floor(-x) end
local function tab() return setmetatable({}, {__index = function(_, k) return trunc(plItemsStats[0][k] or 0) end}) end
-- engine contract under MAW: CalcStatBonusBySkills = 0, CalcStatBonusByItems = itemStats rows
function PlayerMT:GetMeleeDamageMin() return math.max(1, eff(self:GetMight()) + tab()[42]) end
function PlayerMT:GetMeleeDamageMax() return math.max(1, eff(self:GetMight()) + tab()[43]) end
function PlayerMT:GetRangedDamageMin() return math.max(0, tab()[46]) end
function PlayerMT:GetRangedDamageMax() return math.max(0, tab()[47]) end
function PlayerMT:GetMeleeAttack() return eff(self:GetAccuracy()) + tab()[40] end
function PlayerMT:GetRangedAttack() return eff(self:GetAccuracy()) + tab()[44] end
-- CalcStatBonusByItems(AC) = tab[10] - effect(Speed) (zzMaw-Items.lua:2581-2583); the engine adds effect(Speed) back
function PlayerMT:GetArmorClass() local e = eff(self:GetSpeed()) return math.max(0, trunc(plItemsStats[0][10] - e) + e) end
function PlayerMT:GetResistance(i) return (self.ResBase or 0) + (tab()[i + 1] or 0) end
function PlayerMT:GetFullHP()
	return Game.Classes.HPBase[self.Class] + Game.Classes.HPFactor[self.Class]*(self.LevelBase + eff(self:GetEndurance()))
		+ tab()[8]
end
function PlayerMT:GetFullSP()
	return Game.Classes.SPBase[self.Class] + Game.Classes.SPFactor[self.Class]*self.LevelBase + tab()[9]
end
function PlayerMT:GetAttackDelay(ranged)
	local t = {Player = self, PlayerIndex = self.index, Ranged = ranged and true or false, Result = 100}
	for _, h in ipairs(allHandlers("GetAttackDelay")) do h(t) end
	return t.Result
end
function PlayerMT:IsConscious() return true end
function PlayerMT:DoDamage(d, kind) self.lastReflect = (self.lastReflect or 0) + d end
function PlayerMT:SetRecoveryDelay(d) self.RecoveryDelay = d end
function PlayerMT:GetMainCondition() return 18 end
function PlayerMT:ShowFaceAnimation() end

function makePlayer(o)
	local p = setmetatable({index = 0, Class = o.Class, Face = o.Face or 1, LevelBase = o.Level, LevelBonus = 0,
		Skills = {}, items = {}, SpellBuffs = {}, Weak = 0, Disease1 = 0, Disease2 = 0, Disease3 = 0,
		Unconscious = 0, Dead = 0, Eradicated = 0, Insane = 0, HP = 1, SP = 1000, RecoveryDelay = 0,
		statIx = {Might = 1, Intellect = 2, Personality = 3, Endurance = 4, Accuracy = 5, Speed = 6, Luck = 7}},
		PlayerMT)
	for i = 0, 30 do p.SpellBuffs[i] = {ExpireTime = 0, Power = 0, Skill = 0} end
	for _, n in ipairs({"Might", "Intellect", "Personality", "Endurance", "Accuracy", "Speed", "Luck"}) do
		p[n .. "Base"] = o.Stat; p[n .. "Bonus"] = 0
	end
	for id, sm in pairs(o.Skills) do p.Skills[id] = JoinSkill(sm[1], sm[2]) end
	for slot, it in pairs(o.Items) do p.items[slot] = it end
	p.Name = o.Name or "Hero"
	return p
end

function installParty(p)
	Party[0] = p
	Party.High, Party.Count = 0, 1
	plItemsStats[0] = nil
	itemStats(0)
	-- the GetSkill handler would cap item skill bonus at 2x; none here
	return plItemsStats[0]
end
