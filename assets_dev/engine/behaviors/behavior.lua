-- Shared library for actor behaviour scripts (see ACTOR_SCRIPTING_INVESTIGATION.md and behaviors.yml).
--
-- A behaviour script returns Behavior.define{...}. Handlers receive (self, s, ...): self issues commands for the
-- actor, s is the script's saved state (plain data only: booleans, numbers, strings and nested tables).
-- The native monster AI keeps moving, targeting and attacking; handlers only run on these events:
--
--   onStart(self, s)                 first frame the behaviour runs on the actor
--   onLoad(self, s)                  first frame after a saved game or map revisit restored it
--   onThink(self, s)                 every think_interval seconds (default 0.5) while alive
--   onDamaged(self, s, amount)       health fell by amount
--   onHealthBelow = {[0.6] = fn}     once each, highest first, when health falls to or below the fraction
--   onTimer = {name = fn} or fn(self, s, name)
--   onWardBlocked(self, s, wardId)   a ward stopped a projectile
--   onWardExpired(self, s, wardId)
--   onPerformDone(self, s, clip)
--   onDeath(self, s)
--   An MM9 monster's loop (devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md phase 5; worlds/mm9/behaviors/):
--   onTargetChanged(self, s, target)  the target its loop holds changed (nil: none); target as self:target()
--   onAttackDone(self, s)            an attack ended
--   onHit(self, s, attacker)         it was hit (attacker as a target)
--   onTrigger(self, s, message)      a map trigger (MM9's Trigger <object>, <message>; an arena's trigger event)
--
-- Commands and queries on self:
--   hp() maxHp() hpFraction() position() distanceToParty() isHostile() monsterId() age() random([a [, b]])
--   say(text) playSound(name) effect(id [, scale [, heightFraction]])
--   perform{clip=, seconds=, fallback=, sound=, effect=} isPerforming()
--   addWard{id=, radius=, seconds=, effect=, effectScale=, effectInterval=, visual=} removeWard(id) hasWard(id)
--     visual draws the ward's shield dome: {color = {r, g, b}, intensity = 1, rim = 3, noise = 0.35}; false hides it
--   startTimer(name, seconds) stopTimer(name) hasTimer(name)
--   castNext{spell=, skill=, mastery=} setSpell{spell=, skill=, mastery=, chance=} clearSpell()
--   setAiType("suicide" | "wimp" | "normal" | "aggressive" | nil) setNoFlee(enabled)
--   summon(monsterId [, count [, radius]]) summonAt(monsterId, x, y, z [, count [, spread]])
--   blink() suspendShield([seconds]) restoreShield() leave([effect]) setSpeed(multiplier) setInvulnerable(on)
--   qbit(id) runEvent(eventId) bearingToParty() setArmoredFront([degrees, damageMultiplier])
--   setLeash([radius]) setRangedBand([min, max]) moveTo([x, y, z])
--   An MM9 monster's loop (not saved: set setMm9 in onStart and onLoad):
--   setMm9{drives_attacks=, passive=, ignores_calls=, chase_limit=, turn_degrees=, immune="physical"|false}
--   target() targets([radius]) actor(index) setTarget("party" | actorIndex | nil) attack("attack1"|"attack2"|"spell1"|"spell2")
--   attackReady() attacking() dormant() seesParty() push(distance) trace(text) placement() summonPoints()
--     a target is {kind = "party" | "actor", index =, monster =, distance = <edge>, clear =, height =, hostile =}

Behavior = {}

local knownFields = {
    version = true,
    think_interval = true,
    onStart = true,
    onLoad = true,
    onThink = true,
    onDamaged = true,
    onHealthBelow = true,
    onTimer = true,
    onWardBlocked = true,
    onWardExpired = true,
    onPerformDone = true,
    onDeath = true,
    onTargetChanged = true,
    onAttackDone = true,
    onHit = true,
    onTrigger = true,
}

-- Rejects misspelt handler names, which would otherwise never run. Fields starting with "_" are free for helpers.
function Behavior.define(spec)
    if type(spec) ~= "table" then
        error("Behavior.define expects a table", 2)
    end

    for key in pairs(spec) do
        if type(key) ~= "string" or (not knownFields[key] and key:sub(1, 1) ~= "_") then
            error("unknown behaviour field '" .. tostring(key) .. "'", 2)
        end
    end

    return spec
end

-- Returns true at most once per interval seconds for the given key, using s for storage.
function Behavior.cooldown(self, s, key, interval)
    s._cooldowns = s._cooldowns or {}
    local now = self:age()
    local last = s._cooldowns[key]

    if last ~= nil and now - last < interval then
        return false
    end

    s._cooldowns[key] = now
    return true
end
