-- Worked examples: run MAW's real DamageToMonster / DamageToPlayer pipelines
-- (Modules/MawCore/Damage.lua) on fixed characters, monsters and RNG draws.
dofile("chars.lua")

-- ------------------------------------------------------------ RNG control
-- integer draws math.random(a,b) -> floor((a+b)/2); float draws -> RNG_U
RNG_U = 0.999
local realRandom = math.random
math.random = function(a, b)
	if a == nil then return RNG_U end
	if b == nil then b = a; a = 1 end
	return math.floor((a + b)/2)
end

-- ------------------------------------------------------------ remaining stubs
GetMaxHP = function(pl) return pl:GetFullHP() end
getMaxMana = function(pl) return pl:GetFullSP() end
Game.SpellsTxt = setmetatable({}, {__index = function() return {Name = "Spell"} end})
HPtable = {}
survivalMaps = {}
Game.CurrentPlayer = 0
loadRange("General/zzMAW-Skills.lua", 1494, 1501)
loadRange("General/zzMaw-Monsters.lua", 4370, 4375)
const.MonsterKind.Demon = const.MonsterKind.Demon or 101
const.MonsterKind.Elf = const.MonsterKind.Elf or 102
const.MonsterKind.Ogre = const.MonsterKind.Ogre or 103
const.MonsterKind.Elemental = const.MonsterKind.Elemental or 104
loadRange("General/zzzMaw_Artifacts.lua", 48, 286)
loadRange("General/zzzMaw_Artifacts.lua", 445, 550)
lifeLeech = lifeLeech or {}
totalLevel = {}
basetable = {}
CURRENT_HIT = nil
function WhoHitMonster() return CURRENT_HIT end
function WhoHitPlayer() return CURRENT_HIT end
pickLowestPartyMember = function() return 0, 1 end
loadRange("General/zzMaw-Stats.lua", 5, 12)

local function fmt(x)
	if type(x) ~= "number" then return tostring(x) end
	if x == math.floor(x) then return string.format("%d", x) end
	return string.format("%.4f", x)
end

-- run a pipeline stage by stage, recording t.Result after every stage that changed it
function tracePipe(pipe, t)
	local rows = {}
	local prev = t.Result
	for _, stage in ipairs(pipe.order) do
		for _, h in ipairs(pipe.handlers[stage]) do
			h.fn(t)
			if t.Stop then break end
		end
		if t.Result ~= prev then
			rows[#rows + 1] = string.format("    %-22s %s -> %s", stage, fmt(prev), fmt(t.Result))
			prev = t.Result
		end
		if t.Stop then break end
	end
	return rows
end

-- ------------------------------------------------------------ monster
function makeMonster(L, res)
	local id = 2	-- B tier of family 1 (id % 3 == 2)
	totalLevel[id] = L
	basetable[id] = {FullHP = 100}
	local m = {Id = id, NameId = 0, Level = math.min(L, 255), Resistances = {}, SpellBuffs = {},
		Hostile = true, ShowAsHostile = true, X = 0, Y = 0, Z = 0, AIState = 0, Active = true, BodyRadius = 0,
		Attack1 = {Type = 4, DamageAdd = 0, DamageDiceCount = 2, DamageDiceSides = 10},
		Attack2 = {Type = 0, DamageAdd = 0, DamageDiceCount = 1, DamageDiceSides = 20}}
	for i = 0, 30 do m.SpellBuffs[i] = {ExpireTime = 0, Power = 0} end
	for k, v in pairs(res) do m.Resistances[k] = v end
	function m:GetIndex() return 0 end
	local hp = round(getMonsterHealth(m))
	m.HP, m.FullHP, m.FullHitPoints = hp, hp, hp
	HPtable[id] = round(getMonsterHealth({Id = id, Level = L}, L))
	Map.Monsters = {High = 0, [0] = m}
	return m
end

local RES = {[0] = 50, [1] = 0, [2] = 0, [3] = 0, [4] = 10, [6] = 0, [7] = 0, [8] = 0, [9] = 0, [10] = 20}

-- ------------------------------------------------------------ characters
function champion(L)
	local S = round(estimateStat(L))
	local sk = estimateSkill(L)
	local wsk = round(sk*1.5)
	local am = round(sk)
	local p = makePlayer{Class = 19, Level = L, Stat = S, Name = "Champion", Skills = {
		[const.Skills.Sword] = {wsk, masteryForSkill(wsk)}, [const.Skills.Bow] = {wsk, masteryForSkill(wsk)},
		[const.Skills.Armsmaster] = {am, masteryForSkill(am)}, [const.Skills.Chain] = {am, masteryForSkill(am)},
		[const.Skills.Bodybuilding] = {am, math.min(masteryForSkill(am), 3)}},
		Items = {[1] = makeItem(101, MawCore.ItemLevel.PowerFor(L)), [2] = makeItem(102, MawCore.ItemLevel.PowerFor(L)),
			[3] = makeItem(103, MawCore.ItemLevel.PowerFor(L))}}
	pl = p
	installParty(p)
	p.HP = p:GetFullHP()
	return p, {S = S, wsk = wsk, am = am}
end

function archmage(L)
	local S = round(estimateStat(L))
	local sk = estimateSkill(L)
	local ssk = round(sk*1.5)
	local asc = round(sk)
	local p = makePlayer{Class = 46, Level = L, Stat = S, Name = "ArchMage", Skills = {
		[const.Skills.Fire] = {ssk, masteryForSkill(ssk)}, [const.Skills.Dark] = {ssk, masteryForSkill(ssk)},
		[const.Skills.Earth] = {ssk, masteryForSkill(ssk)},
		[const.Skills.Learning] = {asc, masteryForSkill(asc)}, [const.Skills.Staff] = {ssk, masteryForSkill(ssk)}},
		Items = {[1] = makeItem(104, MawCore.ItemLevel.PowerFor(L))}}
	pl = p
	installParty(p)
	p.HP = p:GetFullHP()
	return p, {S = S, ssk = ssk, asc = asc}
end

-- dragon formulas: MawCore/Classes.lua:715-755 verbatim, locals exposed
do
	local lines, n = {}, 0
	for line in io.lines(MAW .. "Modules/MawCore/Classes.lua") do
		n = n + 1
		if n >= 715 and n <= 755 then lines[#lines + 1] = (line:gsub("\r$", "")) end
	end
	local src = "local Classes = {}\n" .. table.concat(lines, "\n") .. "\nDRAGON = {fang = dragonFangDamage, breath = dragonBreathDamage, rec = dragonRecoveryPerSkill}"
	assert(load(src, "@Classes.lua"))()
end
Game.Classes.HPBase[10], Game.Classes.HPFactor[10] = 50, 5
Game.Classes.SPBase[10], Game.Classes.SPFactor[10] = 60, 0
function dragon(L)
	local S = round(estimateStat(L))
	local sk = round(estimateSkill(L)*1.5)
	local p = makePlayer{Class = 10, Face = 99, Level = L, Stat = S, Name = "Dragon", Skills = {
		[const.Skills.Unarmed] = {sk, masteryForSkill(sk)}, [const.Skills.DragonAbility] = {sk, masteryForSkill(sk)}},
		Items = {}}
	pl = p
	installParty(p)
	-- MawCore/Classes.lua:764-815 dragon CalcStatBonusByItems / GetAttackDelay handlers
	local e = Game.GetStatisticEffect
	function p:GetMeleeDamageMin() return math.max(1, e(self:GetMight()) + trunc(DRAGON.fang(self, 0.75))) end
	function p:GetMeleeDamageMax() return math.max(1, e(self:GetMight()) + trunc(DRAGON.fang(self, 1.25))) end
	function p:GetRangedDamageMin() return trunc(DRAGON.breath(self, 0.75)) end
	function p:GetRangedDamageMax() return trunc(DRAGON.breath(self, 1.25)) end
	local baseDelay = p.GetAttackDelay
	function p:GetAttackDelay(ranged)
		local r = baseDelay(self, ranged)
		local id = ranged and const.Skills.DragonAbility or const.Skills.Unarmed
		return r*(1 + DRAGON.rec*SplitSkill(self:GetSkill(id)))
	end
	p.HP = p:GetFullHP()
	return p, {S = S, sk = sk}
end

-- ------------------------------------------------------------ scenarios
local out = {}
local function say(...) out[#out + 1] = table.concat({...}, " ") end

local function hitMonster(title, p, mon, hit, kind, engineDamage)
	CURRENT_HIT = hit
	mapvars = {}
	local t = {DamageKind = kind, Damage = engineDamage, Result = engineDamage, Player = p, PlayerIndex = 0,
		MonsterIndex = 0, Monster = mon, ByPlayer = true}
	say("  " .. title .. string.format(" (U=%s): engine Damage in = %s", RNG_U, fmt(engineDamage)))
	for _, r in ipairs(tracePipe(MawCore.Damage.pipe, t)) do say(r) end
	say("    => final " .. fmt(t.Result))
	return t.Result
end

local function spellBase(p, spell, skillId, kindName)
	local s, m = SplitSkill(p:GetSkill(skillId))
	CURRENT_HIT = {Player = p, Object = {Bits = 0, Spell = spell, SpellType = spell, SpellMastery = m, SpellSkill = s}, Spell = spell}
	local t = {Spell = spell, Skill = s, Mastery = m, HP = 0, Result = 0}
	lastHandler("CalcSpellDamage")(t)
	return t.Result, s, m
end

local function hitPlayer(title, p, mon, action, kind, object)
	CURRENT_HIT = {Monster = mon, MonsterIndex = 0, MonsterAction = action, Object = object}
	local t = {DamageKind = kind, Damage = 100, Result = 100, Player = p, PlayerIndex = 0}
	say("  " .. title .. ": engine Damage in = 100 (discarded)")
	for _, r in ipairs(tracePipe(MawCore.Damage.playerPipe, t)) do say(r) end
	say("    => final " .. fmt(t.Result))
end

for _, bolster in ipairs({100, 200}) do
	for _, L in ipairs({50, 150}) do
		Game.BolsterAmount = 100	-- characters are built from the MAW-difficulty model
		vars.MMLVL = {L, 0, 0, 0}
		local p, info = champion(L)
		Game.BolsterAmount = bolster
		local mon = makeMonster(L, RES)
		say(string.format("== bolster %d (difficulty %d), level %d", bolster, GetDifficulty(), L))
		say(string.format("  monster: B-tier, level %d, HP %d, res fire 50 / phys 10 / dark 20 / rest 0;" ..
			" getMonsterDamage %.4f; HPtable %d", L, mon.FullHP, getMonsterDamage(mon), HPtable[2]))
		say(string.format("  Champion: stats %d, sword/bow %d, armsmaster/chain/bodybuilding %d; melee %d-%d atk %d" ..
			" delay %d mult %.6f; bow %d-%d atk %d delay %d mult %.6f; AC %d, res(fire) %d, HP %d",
			info.S, info.wsk, info.am, p:GetMeleeDamageMin(), p:GetMeleeDamageMax(), p:GetMeleeAttack(),
			p:GetAttackDelay(false), damageMultiplier[0].Melee, p:GetRangedDamageMin(), p:GetRangedDamageMax(),
			p:GetRangedAttack(), p:GetAttackDelay(true), damageMultiplier[0].Ranged, p:GetArmorClass(),
			p:GetResistance(10), p:GetFullHP()))
		local critC, critM = getCritInfo(p, false, L)
		say(string.format("  melee hit chance %.4f, ranged %.4f, crit chance %.4f, crit mult %.2f, chance to be hit %.4f",
			MawCore.Formulas.mawPlayerHitChance(p, mon, 0, 0), MawCore.Formulas.mawPlayerHitChance(p, mon, 1, 0),
			critC, critM, MawCore.Formulas.chanceToBeHit(p:GetSpeed(), L)))
		for _, u in ipairs({0.999, 0.0}) do
			RNG_U = u
			hitMonster("melee 2H sword", p, mon, {Player = p}, 4, 10)
			hitMonster("bow", p, mon, {Player = p, Object = {Bits = 0, Spell = 133, SpellType = 133, Item = makeItem(0)}, Spell = 133},
				4, 10)
		end
		RNG_U = 0.999
		-- monster attacks the champion
		RNG_U = 0.5
		local realDodge = MawRollDodge
		MawRollDodge = function() return true end
		hitPlayer("monster melee (Attack1, phys)", p, mon, 0, 4, nil)
		hitPlayer("monster Fireball (spell 6, fire)", p, mon, 2, 0, {Bits = 0, Spell = 6, SpellType = 6})
		MawRollDodge = realDodge
		RNG_U = 0.999

		-- caster
		Game.BolsterAmount = 100
		local c, ci = archmage(L)
		Game.BolsterAmount = bolster
		mon = makeMonster(L, RES)
		local sc, sm = getCritInfo(c, "spell")
		say(string.format("  ArchMage: stats %d, fire/dark/staff %d, ascension %d; spell crit chance %.4f (vs ref level %d)," ..
			" spell crit mult %.2f; fireball delay %d, dragon breath delay %d", ci.S, ci.ssk, ci.asc, sc, MawReferenceLevel(),
			sm, getSpellDelay(c, 6), getSpellDelay(c, 97)))
		for _, u in ipairs({0.999, 0.0}) do
			RNG_U = u
			local dmg, s, m = spellBase(c, 6, const.Skills.Fire)
			local dmin, dmax, dadd = ascendSpellDamage(ci.asc, masteryForSkill(ci.asc), 6)
			say(string.format("  Fireball CalcSpellDamage: skill %d mastery %d dice 1..%d add %d -> %s", s, m, dmax, dadd, fmt(dmg)))
			hitMonster("Fireball", c, mon, CURRENT_HIT, const.Damage.Fire, dmg)
			local dmg2, s2, m2 = spellBase(c, 97, const.Skills.Dark)
			local _, dmax2, dadd2 = ascendSpellDamage(ci.asc, masteryForSkill(ci.asc), 97)
			say(string.format("  Dragon Breath CalcSpellDamage: skill %d mastery %d dice 1..%d add %d -> %s", s2, m2, dmax2,
				dadd2, fmt(dmg2)))
			hitMonster("Dragon Breath", c, mon, CURRENT_HIT, const.Damage.Dark, dmg2)
		end
		RNG_U = 0.999
		do
			local s, m = SplitSkill(c:GetSkill(const.Skills.Earth))
			CURRENT_HIT = {Player = c, Object = {Bits = 0, Spell = 44, SpellType = 44, SpellMastery = m, SpellSkill = s}, Spell = 44}
			local t = {Spell = 44, Skill = s, Mastery = m, HP = mon.HP, Result = 0}
			lastHandler("CalcSpellDamage")(t)
			say(string.format("  Mass Distortion CalcSpellDamage: proxy HP %d, skill %d -> %s", mon.HP, s, fmt(t.Result)))
			hitMonster("Mass Distortion", c, mon, CURRENT_HIT, const.Damage.Earth, t.Result)
		end
		if bolster == 100 then
			Game.BolsterAmount = 100
			local d, di = dragon(L)
			mon = makeMonster(L, RES)
			say(string.format("  Dragon (class 10): stats %d, unarmed/dragon %d; fang %d-%d delay %s; breath %d-%d delay %s",
				di.S, di.sk, d:GetMeleeDamageMin(), d:GetMeleeDamageMax(), d:GetAttackDelay(false),
				d:GetRangedDamageMin(), d:GetRangedDamageMax(), d:GetAttackDelay(true)))
			for _, u in ipairs({0.999, 0.0}) do
				RNG_U = u
				hitMonster("dragon fang (melee)", d, mon, {Player = d}, 4, 10)
				hitMonster("dragon breath (kind 50)", d, mon, {Player = d, Object = {Bits = 0, Spell = 0, SpellType = 0}}, 50, 10)
			end
			RNG_U = 0.999
		end
		RNG_U = 0.999
	end
end
print(table.concat(out, "\n"))
