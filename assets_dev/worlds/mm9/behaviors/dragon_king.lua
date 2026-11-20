-- The Dragon King (MM9 Dragon.scr, row 212; devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "Phase 5").
--
-- He never moves. His MM9 loop holds and faces a target (FaceObject at 180 degrees a second) and attacks only when
-- this script says: under 200 LT a wing buffet (21 in 101: no damage, a push) or the breath, under 230 LT the breath,
-- under 1 800 LT the fire bolt, beyond that nothing. After each attack he may switch targets among everyone in reach:
-- he hates every AI (AddEnemy AIBase: worlds/mm9/relations.yml) and the party. Hidden at the start (ScriptParams 1,
-- the map's dormant start) he lands and taunts once woken (the map's DragonTrigger: evt.WakeActor), then attacks the
-- party. The Winged Mutant reinforcements, his reward and the trigger are the map's (dragonstadium.lua).
--
-- Distances are ours (MM9's LithTech units x 2.56); MM9's AIGetDistance is edge to edge (target.distance).

local LT = 2.56
local WING_ATTACK_DIST = 200 * LT
local BREATH_ATTACK_DIST = 230 * LT
local MAX_ATTACK_DIST = 1800 * LT
-- GetDims' z, the body's half depth (MM9's 200 LT; assumed equal to its radius): a target higher above his feet gets
-- the fire-bolt clip instead of the breath (DoBreathAttack).
local DIMS_Z = 200 * LT
local WING_ATTACK_CHANCE = 20
local MIN_ATTACK_WAIT = 0.2
local MAX_ATTACK_WAIT = 0.6
local MIN_SAME_TARGET_TIME = 3.0
local MAX_SAME_TARGET_TIME = 6.0
local CANT_ATTACK_RETRY = 0.2
-- The model's WingAttack clip and its wing clap (actors.yml attack_melee impact); the push is ours (assumed).
local WING_SECONDS = 1.0
local WING_CLAP_SECONDS = 0.533
local WING_PUSH_DISTANCE = 512
-- The model's Land and Taunt clips.
local LAND_SECONDS = 5.8
local TAUNT_SECONDS = 2.2
-- An attack it asked for has started by then, else it was dropped (no target offered this step).
local ATTACK_START_SECONDS = 0.25
-- DoBreathing (NormalSetup, OnLanded): DoClientFX "dragon smoke" every 2.5 s (Wait BREATHING_WAIT, 2.5), MM9's
-- snout nodes 8 and 9; here at the model's Socket_Mouth (bind pose: 1 507 up, 496 forward at scale 100).
local BREATH_SMOKE_SECONDS = 2.5
local SNOUT_HEIGHT_FRACTION = 0.87
local SNOUT_FORWARD = 496

local function same(a, b)
    if a == nil or b == nil then
        return a == b
    end

    return a.kind == b.kind and a.index == b.index
end

local function key(target)
    return target and {kind = target.kind, index = target.index} or nil
end

local function name(target)
    if target == nil then
        return "none"
    end

    return target.kind == "party" and "party" or ("actor:" .. target.index)
end

local function setUp(self, s)
    -- Dragon.scr includes no AICommon.inc: no alerts either way, no 30 s give-up (only OnLostTarget, TargetTooFar).
    self:setMm9{drives_attacks = true, ignores_calls = true, chase_limit = 0, turn_degrees = 180,
        passive = s.hidden == true or s.landing == true or s.taunting == true}
end

-- SetupAttack: the next attack 0.2-0.6 s from now.
local function setupAttack(self, s)
    local wait = MIN_ATTACK_WAIT + (MAX_ATTACK_WAIT - MIN_ATTACK_WAIT) * self:random()
    self:startTimer("attack", wait)
end

-- SetupNewTarget.
local function setupNewTarget(self, s, target)
    s.lastSwitch = self:age()
    s.hurry = 0
    s.target = key(target)
end

-- CheckClearShot (Dragon.scr:551-578), MM9 quirk reproduced: without a clear shot it rolls the 75 % "ignore" chance
-- and then leaves bClearShot FALSE either way, so a target beyond breath range without a clear shot is never taken.
local function clearShot(self, target)
    if target.clear then
        return true
    end

    self:random(0, 100)
    return false
end

-- FindTarget (Dragon.scr:581-737).
local function findTarget(self, s)
    -- Half the time it first looks within its wing distance (g_nTemp's 50/20 is computed and never used: quirk).
    local list = {}

    if self:random(0, 100) < 50 then
        list = self:targets(WING_ATTACK_DIST)
    end

    if #list == 0 then
        list = self:targets()
    end

    if #list == 0 then
        return nil, "none"
    end

    -- The last attacker first, the more likely the nearer it is in the list (index / count x 100 + 15).
    if s.lastAttacker ~= nil then
        for index, target in ipairs(list) do
            if same(key(target), s.lastAttacker) then
                if self:random(0, 100) > (index - 1) / #list * 100 + 15
                    and (target.distance < BREATH_ATTACK_DIST or clearShot(self, target)) then
                    return target, "last_attacker"
                end

                break
            end
        end
    end

    -- The first one in range with a shot that is not the current target. MM9 quirk reproduced: a candidate skipped
    -- for its shot or range stays found, so the last one in the list is taken when none qualifies (unless it is the
    -- current target).
    local current = s.target
    local found = nil

    for _, target in ipairs(list) do
        found = target

        if same(key(target), current) then
            found = nil
        elseif target.distance >= BREATH_ATTACK_DIST and not clearShot(self, target) then
            -- next
        elseif target.distance > MAX_ATTACK_DIST then
            -- next
        else
            return target, "first"
        end
    end

    return found, "last"
end

local function newTarget(self, s, target, note)
    self:setTarget(target.kind == "party" and "party" or target.index)
    setupNewTarget(self, s, target)
    s.pending = key(target)
    self:trace("switch " .. name(target) .. " " .. note)
end

-- MaybeSwitchTarget (Dragon.scr:740-806): not within 3 s of the last switch (less what hits by others hurried it);
-- after 6 s a found target always replaces the current; else 20 %, 80 % for a nearer one, +45 % for the last
-- attacker (GetRandomInt 0, 100 at most the chance: n + 1 in 101).
local function maybeSwitchTarget(self, s)
    local now = self:age()

    if now - MIN_SAME_TARGET_TIME + s.hurry < s.lastSwitch then
        return
    end

    local found, how = findTarget(self, s)

    if found == nil then
        return
    end

    local current = self:target()

    if s.target == nil or current == nil then
        newTarget(self, s, found, how)
        return
    end

    if same(key(found), s.target) then
        return
    end

    local chance = 20

    if current.distance > found.distance then
        chance = 80
    end

    if same(key(found), s.lastAttacker) then
        chance = chance + 45
    end

    if now - MAX_SAME_TARGET_TIME + s.hurry > s.lastSwitch then
        newTarget(self, s, found, how .. " held")
        return
    end

    local roll = self:random(0, 100)

    if roll > chance then
        self:trace("keep " .. name(s.target) .. " over " .. name(found) .. " chance " .. chance .. " roll " .. roll)
        return
    end

    newTarget(self, s, found, how .. " chance " .. chance .. " roll " .. roll)
end

-- CantAttackRightNow: again in 0.2 s (traced when the reason changes).
local function cantAttack(self, s, why)
    s.attacking = false

    if s.waiting ~= why then
        s.waiting = why
        self:trace("wait " .. why)
    end

    self:startTimer("attack", CANT_ATTACK_RETRY)
end

local function startAttack(self, s, ability, what, target)
    s.waiting = nil
    self:attack(ability)
    s.attacking = true
    s.starting = true
    self:startTimer("attack_start", ATTACK_START_SECONDS)
    self:trace(what .. " " .. name(s.target) .. " distance " .. math.floor(target.distance))
end

-- DoBreathAttack: rAttack1 (the fire-bolt clip and bolt) at a target higher than DIMS_Z above its feet, else
-- rAttack3 (the breath: its first spell, Incinerate).
local function breathAttack(self, s, target)
    if target.height > DIMS_Z then
        startAttack(self, s, "attack1", "breath_high", target)
    else
        startAttack(self, s, "spell1", "breath", target)
    end
end

-- DoCloseAttack: the hand attack's roll (its use is commented out in Dragon.scr), then 21 in 101 the wing, else the
-- breath; either only with its attack ready (CanAttack).
local function closeAttack(self, s, target)
    self:random(0, 100)
    local roll = self:random(0, 100)

    if not self:attackReady() then
        cantAttack(self, s, "not_ready")
        return
    end

    if roll > WING_ATTACK_CHANCE then
        breathAttack(self, s, target)
        return
    end

    s.attacking = true
    s.waiting = nil
    s.wing = true
    self:perform{fallback = "attack_melee", seconds = WING_SECONDS}
    self:startTimer("wing_clap", WING_CLAP_SECONDS)
    self:trace("wing " .. name(s.target) .. " distance " .. math.floor(target.distance) .. " roll " .. roll)
end

-- DoAttack (Dragon.scr:259-298).
local function doAttack(self, s)
    local target = self:target()

    if target == nil or s.target == nil then
        s.attacking = false
        return
    end

    if not target.offered then
        cantAttack(self, s, "no_target")
        return
    end

    if target.distance < WING_ATTACK_DIST then
        closeAttack(self, s, target)
        return
    end

    -- CanRangeAttack: its attack ready and a line to the target.
    if not self:attackReady() or not target.clear then
        cantAttack(self, s, self:attackReady() and "no_shot" or "not_ready")
        return
    end

    if target.distance < BREATH_ATTACK_DIST then
        breathAttack(self, s, target)
    elseif target.distance < MAX_ATTACK_DIST then
        startAttack(self, s, "attack1", "bolt", target)
    else
        s.attacking = false
        self:trace("out_of_range " .. name(s.target))
        setupAttack(self, s)
    end
end

local function breatheSmoke(self)
    self:effect("mm9:dragon_smoke", 1.0, SNOUT_HEIGHT_FRACTION, SNOUT_FORWARD)
    self:startTimer("breath_smoke", BREATH_SMOKE_SECONDS)
end

-- AttackDone and WingAttackDone.
local function attackDone(self, s, wing)
    s.attacking = false

    if wing then
        -- SetupPostWingAttack: straight to the next attack.
        doAttack(self, s)
        return
    end

    maybeSwitchTarget(self, s)

    if s.target ~= nil then
        setupAttack(self, s)
    end
end

return Behavior.define{
    version = 1,
    -- MM9 updates its actors ten times a second (OnTargetBeyondDist's check).
    think_interval = 0.1,

    onStart = function(self, s)
        s.lastSwitch = 0
        s.hurry = 0
        s.hidden = self:dormant()
        setUp(self, s)
    end,

    onLoad = function(self, s)
        setUp(self, s)

        if not s.hidden and not s.landing and self:hp() > 0 and not self:hasTimer("breath_smoke") then
            self:startTimer("breath_smoke", BREATH_SMOKE_SECONDS)
        end
    end,

    onThink = function(self, s)
        -- Woken (OnTrigger): Land, then Taunt, then the party (TauntDone: NormalSetup, GetPlayerHandle).
        if s.hidden and not self:dormant() then
            s.hidden = false
            s.landing = true
            setUp(self, s)
            self:perform{clip = "land", seconds = LAND_SECONDS, fallback = "standing"}
            self:trace("land")
            return
        end

        -- TargetTooFar: beyond MAX_ATTACK_DIST it lets its target go and idles.
        local target = self:target()

        if target ~= nil and target.distance > MAX_ATTACK_DIST then
            self:setTarget(nil)
            s.target = nil
            s.attacking = false
            self:stopTimer("attack")
            self:trace("too_far " .. name(target))
        end
    end,

    -- The loop took a target (OnFoundTarget within its sight, or OnDamage without one) or lost it.
    onTargetChanged = function(self, s, target)
        if target ~= nil then
            if same(key(target), s.pending) then
                s.pending = nil
                return
            end

            setupNewTarget(self, s, target)
            self:trace("found " .. name(target))

            if not s.attacking then
                setupAttack(self, s)
            end

            return
        end

        local previous = s.target
        s.target = nil
        s.pending = nil
        self:stopTimer("attack")

        -- OnTargetDead (TargetDead): look for the next one at once. Its target is dead when it is no longer among the
        -- living; otherwise it lost it (OnLostTarget) and idles.
        if previous ~= nil then
            for _, other in ipairs(self:targets()) do
                if same(key(other), previous) then
                    self:trace("lost " .. name(previous))
                    return
                end
            end

            local found, how = findTarget(self, s)

            if found ~= nil then
                newTarget(self, s, found, "dead " .. how)
                setupAttack(self, s)
            end
        end
    end,

    -- OnDamage: the last attacker gets priority; a hit by another than its target hurries the next switch by 0.5 s,
    -- 20 in 101 (GetRandomInt 0, 100 > 80).
    onHit = function(self, s, attacker)
        if not same(key(attacker), s.lastAttacker) then
            s.lastAttacker = key(attacker)
        end

        if s.target ~= nil and not same(key(attacker), s.target) then
            local roll = self:random(0, 100)

            if roll > 80 then
                s.hurry = s.hurry + 0.5
                self:trace("hurry " .. s.hurry .. " roll " .. roll)
            end
        end
    end,

    onAttackDone = function(self, s)
        s.starting = false
        attackDone(self, s, false)
    end,

    onPerformDone = function(self, s)
        if s.landing then
            s.landing = false
            s.taunting = true
            breatheSmoke(self)   -- OnLanded: DoBreathing
            self:perform{clip = "taunt", seconds = TAUNT_SECONDS, fallback = "standing"}
            self:trace("taunt")
        elseif s.taunting then
            s.taunting = false
            setUp(self, s)
            self:setTarget("party")
            setupNewTarget(self, s, {kind = "party"})
            s.pending = {kind = "party"}
            self:trace("found party fly_in")
            setupAttack(self, s)
        elseif s.wing then
            s.wing = false
            attackDone(self, s, true)
        end
    end,

    onTimer = {
        attack = function(self, s)
            doAttack(self, s)
        end,

        -- The attack it asked for never started (its target was not offered that step): it tries again.
        attack_start = function(self, s)
            if s.starting and not self:attacking() then
                s.starting = false
                cantAttack(self, s, "dropped")
            end
        end,

        breath_smoke = function(self, s)
            breatheSmoke(self)
        end,

        -- The wing buffet does no damage: it pushes its target away at the clap.
        wing_clap = function(self, s)
            self:push(WING_PUSH_DISTANCE)
            self:trace("wing_push " .. name(s.target))
        end,
    },
}
