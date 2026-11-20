-- Harness: loads MAW's real Lua (selected files and line ranges) under Lua 5.4
-- with small MMExt/Lua 5.1 shims, so the formulas run verbatim.
MAW = "/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/"
REF = "/home/pjasicek/github/OpenYAMM/reference/mmmerge/Scripts/"

local noop = function() end

-- ---------------------------------------------------------------- shims
unpack = table.unpack
math.pow = function(a, b) return a ^ b end
loadstring = load
function table.find(t, v) for k, v1 in pairs(t) do if v1 == v then return k end end end
function table.invert(t) local r = {} for k, v in pairs(t) do r[v] = k end return r end
function table.copy(s, d) d = d or {} for k, v in pairs(s) do d[k] = v end return d end
-- MAW's own round (zz_Maw-initialize.lua:315): half up, = floor(x+0.5)
function round(x) if x % 1 >= 0.5 then x = x - x % 1 + 1 else x = x - x % 1 end return x end
-- MMExt math.round = bit.tobit: LuaJIT rounds half to even
math.round = function(x)
	local f = math.floor(x)
	local d = x - f
	if d > 0.5 then return f + 1 elseif d < 0.5 then return f end
	if f % 2 == 0 then return f end
	return f + 1
end
bit = {And = function(a, b) return a & b end}

-- MMMerge skill packing (Structs/After/RemoveSkillValueLimits.lua)
function SplitSkill(val)
	if not val then return end
	local n = val % 1024
	local m = 0
	if val >= 4096 then m = 4 elseif val >= 2048 then m = 3 elseif val >= 1024 then m = 2 elseif val >= 1 then m = 1 end
	return n, m
end
function JoinSkill(s, m)
	local bits = ({[0] = 0, [1] = 0, [2] = 1024, [3] = 2048, [4] = 4096})[m]
	return s + bits
end

-- ---------------------------------------------------------------- const
offsets = {MMVersion = 8, PatchDll = {}}
internal = {MMVersion = 8}
mem = {dll = setmetatable({}, {__index = function() return {} end}), i4 = {}, u4 = {}, u1 = {},
	hook = noop, autohook = noop, autohook2 = noop, asmpatch = noop, asmhook = noop, call = noop,
	hookfunction = noop, IgnoreProtection = noop, nop = noop}
AppPath = ""
dofile(REF .. "Core/ConstAndBits.lua")
const.Race = {Human = 0, Vampire = 1, DarkElf = 2, Minotaur = 3, Troll = 4, Dragon = 5, Undead = 6, Elf = 7,
	Goblin = 8, Dwarf = 9, Zombie = 10}
const.Class = const.Class or {}
const.Class.Thief, const.Class.Rogue, const.Class.Assassin, const.Class.Spy = 34, 35, 36, 37
const.Class.Dragon, const.Class.GreatWyrm, const.Class.Lich = 10, 11, 45

-- ---------------------------------------------------------------- engine stubs
events = setmetatable({_h = {}}, {
	__newindex = function(t, k, f) t._h[k] = t._h[k] or {}; table.insert(t._h[k], f) end,
	__index = function(t, k)
		if k == "call" or k == "cocalls" or k == "Remove" then return noop end
		return nil
	end})
function lastHandler(name) local l = events._h[name]; return l and l[#l] end
function allHandlers(name) return events._h[name] or {} end

RunNextTick = noop
vars = {MAWSETTINGS = {buffRework = "ON", friendlyDamage = "OFF"}, legendaries = {}, mawbuff = {},
	MMLVL = {0, 0, 0, 0}, normalEnchantResistance = {}, shieldEnchant = {}}
mapvars = {}
Skillz = {get = function(pl, id) return pl.Skills[id] or 0 end, setDesc = noop, getDesc = function() return "" end}

-- vanilla parameter table (MM8) for statistic values below 25
local thr = {500, 400, 350, 300, 275, 250, 225, 200, 175, 150, 125, 100, 75, 50, 40, 35, 30, 25, 21, 19, 17, 15, 13,
	11, 9, 7, 5, 3, 0}
local val = {30, 25, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -5, -6}
local function vanillaEffect(v)
	for i = 1, #thr do if v >= thr[i] then return val[i] end end
	return -6
end
local function statEffect(v)
	-- MAW zzMaw-Stats.lua:947-951 GetStatisticEffect override
	if v >= 25 then return math.floor(v / 5) end
	return vanillaEffect(v)
end

local function buffs(n)
	local t = {}
	for i = 0, n do t[i] = {ExpireTime = 0, Power = 0, Skill = 0} end
	return t
end

Game = {BolsterAmount = 100, Time = 10000000, TurnBased = false, freeProgression = true,
	GetStatisticEffect = statEffect,
	CharacterPortraits = setmetatable({}, {__index = function(t, k)
		local race = (k == 99) and const.Race.Dragon or const.Race.Human
		return {Race = race}
	end}),
	PlaceMonTxt = setmetatable({}, {__index = function() return "Monster" end}),
	MonstersTxt = setmetatable({}, {__index = function() return {Name = "Monster"} end}),
	ShowStatusText = noop, ItemsTxt = {High = 2500}, Classes = {HPBase = {}, HPFactor = {}, SPBase = {}, SPFactor = {}},
	Spells = setmetatable({}, {__index = function(t, k) local s = {} rawset(t, k, s) return s end}),
}
Party = {High = 0, Count = 1, SpellBuffs = buffs(30), X = 0, Y = 0, Z = 0, Direction = 0,
	EnemyDetectorRed = true, EnemyDetectorYellow = false}
Map = {Monsters = {High = -1}, IsIndoor = function() return false end, IsOutdoor = function() return true end,
	Name = "test.odm", IndoorOrOutdoor = 2, MapStatsIndex = 1}
Multiplayer = nil
StrColor = function(r, g, b, s) return tostring(s) end
shortenNumber = function(n) return n end
checkSkills = noop
evt = setmetatable({}, {__index = function() return {Add = noop} end})
getMapAffixPowerTable = {}
function getMapAffixPower(n) return getMapAffixPowerTable[n] or false end
TownPortalControls = {MapOfContinent = function() return 1 end}
Mouse = {Item = {}}

-- class id lists (MawCore/Classes.lua:646-656)
seraphClass, shamanClass, dkClass, elementalistClass = {53, 54, 55}, {59, 60, 61}, {56, 57, 58}, {62, 63, 64}
assassinClass = {34, 35, 36, 37}
twoHandedAxes, oneHandedAxes = {}, {}
artArmors, artWeap1h, artWeap2h, ancientWeapons = {}, {}, {}, {}

-- ---------------------------------------------------------------- loaders
function loadRange(file, a, b)
	local lines = {}
	local n = 0
	for line in io.lines(MAW .. file) do
		n = n + 1
		if n >= a and n <= b then lines[#lines + 1] = (line:gsub("\r$", "")) end
		if n > b then break end
	end
	-- keep line numbers aligned for error messages
	local src = string.rep("\n", a - 1) .. table.concat(lines, "\n")
	local f, err = load(src, "@" .. file)
	if not f then error(err) end
	f()
end
function loadFile(file) loadRange(file, 1, 1e9) end

MawCore = {}
MawCore.Sync = {inGame = function() return false end, monsterBuffChanged = noop, monsterStackAdded = noop,
	isClient = function() return false end}
MawCore.Save = {data = function() return {} end}
MawCore.Artifacts = {BaseMult = function() return 1 end, BonusesOf = function() return nil end}
loadFile("Modules/MawCore/Formulas.lua")
loadFile("Modules/MawCore/ItemLevel.lua")
loadFile("Modules/MawCore/Pipeline.lua")
loadFile("Modules/MawCore/DamageState.lua")
loadFile("Modules/MawCore/MonsterHP.lua")
loadFile("Modules/MawCore/Estimates.lua")

-- zzMaw-Items.lua: loot strength, rarity model, enchant damage, aura, weapon level damage
loadRange("General/zzMaw-Items.lua", 444, 561)
loadRange("General/zzMaw-Items.lua", 574, 878)
loadRange("General/zzMaw-Items.lua", 889, 893)
loadRange("General/zzMaw-Items.lua", 2047, 2155)
loadRange("General/zzMaw-Items.lua", 4283, 4319)
loadRange("General/zzMaw-Items.lua", 4390, 4404)
loadRange("General/zzMaw-Items.lua", 4555, 4607)
-- zzMAW-Skills.lua: skill tables, recovery, GetAttackDelay
loadRange("General/zzMAW-Skills.lua", 24, 174)
loadRange("General/zzMAW-Skills.lua", 402, 617)
-- zzMaw-Stats.lua: crit, spell delay, might, mitigation, difficulty, mastery helpers
loadRange("General/zzMaw-Stats.lua", 52, 142)
loadRange("General/zzMaw-Stats.lua", 162, 245)
loadRange("General/zzMaw-Stats.lua", 253, 267)
loadRange("General/zzMaw-Stats.lua", 296, 298)
loadRange("General/zzMaw-Stats.lua", 719, 1158)
loadRange("General/zzMaw-Stats.lua", 1462, 1530)
-- zzMaw-Spells.lua: heal personality, spell powers, CalcSpellDamage, buff power, CC
loadRange("General/zzMaw-Spells.lua", 80, 83)
loadRange("General/zzMaw-Spells.lua", 1337, 1351)
loadRange("General/zzMaw-Spells.lua", 1892, 1933)
loadRange("General/zzMaw-Spells.lua", 1937, 2094)
loadRange("General/zzMaw-Spells.lua", 2655, 2692)
-- zzMaw-Monsters.lua: tier helpers, monster level, monster spell multipliers
loadRange("General/zzMaw-Monsters.lua", 18, 40)
loadRange("General/zzMaw-Monsters.lua", 1884, 1895)
loadRange("General/zzMaw-Monsters.lua", 1938, 1962)
-- legendaries / mana shield
loadRange("Global/zzMaw_Legendaries.lua", 61, 102)
-- the pipelines themselves
loadFile("Modules/MawCore/Damage.lua")

-- buff mapping: Global/zzMaw_Mapping.lua AfterLoadMap replaces buffPower (no affix 33)
buffPower = {
	[3] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[14] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[25] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[36] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[58] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[69] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[5] = {Base = {[0] = 0, 10, 10, 10, 10}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[17] = {Base = {[0] = 0, 15, 15, 15, 15}, Scaling = {[0] = 0, 3, 3, 3, 3}},
	[28] = {Base = {[0] = 0, 15, 15, 15, 15}, Scaling = {[0] = 0, 3, 3, 3, 3}},
	[38] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[46] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[47] = {Base = {[0] = 0, 5, 5, 5, 5}, Scaling = {[0] = 0, 1, 1, 1, 1}},
	[51] = {Base = {[0] = 0, 15, 15, 15, 15}, Scaling = {[0] = 0, 3, 3, 3, 3}},
	[56] = {Base = {[0] = 0, 10, 10, 10, 10}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[71] = {Base = {[0] = 0, 5, 5, 5, 5}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[73] = {Base = {[0] = 0, 15, 15, 15, 15}, Scaling = {[0] = 0, 3, 3, 3, 3}},
	[83] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[85] = {Base = {[0] = 0, 20, 20, 20, 20}, Scaling = {[0] = 0, 2, 2, 2, 2}},
	[86] = {Base = {[0] = 0, 10, 10, 10, 10}, Scaling = {[0] = 0, 2, 2, 2, 2}},
}

-- buff sources: none unless a scenario sets them
buffSkills = {}
function getBuffSkill(spell) local b = buffSkills[spell]; if b then return b[1], b[2], b[3] end return 0, 0, 0 end
function bestBuffSource(spell) return getBuffSkill(spell) end
function potionBuffActive() return false end
function getTotalLevel() local r = 0 for i = 1, 4 do r = r + vars.MMLVL[i] end return r end
loadRange("General/zzzMaw_Experience.lua", 278, 290)
IsArtifactItem = function() return false end
IsArtifactWeapon = function() return false end
ItemQualityMult = function() return 1 end

-- MM8 MonsterBuff ids live under const.MonsterBuff; make sure DamageHalved etc exist
assert(const.MonsterBuff.DamageHalved == 23 and const.MonsterBuff.ShrinkingRay == 3)

-- zzMaw-Spells.lua:1888 damage spell list (assigned inside GameInitialized2)
spells = {2,6,7,8,9,10,11,15,18,20,22,24,26,29,32,37,39,41,43,44,52,59,65,70,76,78,79,84,87,90,93,97,98,99,103,111,123}
-- oldTable[spell][mastery] = base delays from MAW Data/Tables/Spells2.txt (zzMaw-Stats.lua:148-154)
oldTable = {}
do
	local n = 0
	for line in io.lines("/home/pjasicek/github/Maw-Mod-MMMerge/Data/Tables/Spells2.txt") do
		n = n + 1
		if n >= 2 then
			local f = {}
			for c in (line:gsub("\r$", "") .. "\t"):gmatch("([^\t]*)\t") do f[#f + 1] = c end
			local id = n - 2
			oldTable[id] = {tonumber(f[6]) or 0, tonumber(f[7]) or 0, tonumber(f[8]) or 0, tonumber(f[9]) or 0}
			oldTable[id][0] = oldTable[id][1]
		end
	end
end
loadRange("General/zzMaw-Spells.lua", 1018, 1018)
loadRange("General/zzClasses.lua", 455, 469)
