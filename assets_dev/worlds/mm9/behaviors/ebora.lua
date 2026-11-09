-- Ebora (MM9 row 301; devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "Phase 5"), by her placement's script:
--
--   eborabath.scr (the Bathhouse): she never fights (her OnLaunchDone's SetupTarget and AggressiveStart are commented
--   out) and no blow hurts her (CanDamage FALSE). The first time she sees the party she launches (her Launch clip;
--   RolloverText 14). Each concubine that dies taunts (RolloverText 8 + n); the third (or her fat friend's death,
--   DeadPal) sends her off: Launch, CastSpell, a column of fire, gone a second later. The keys and experience of her
--   escape are the map's (bathhouse.lua), whose handler also removes her at once on the third death.
--   eboramines.scr (Thjorad Mine): she stands until the map's FreeAtLast trigger or a hit, then fidgets 3 s, taunts
--   5 s (RolloverText 8), casts 2 s and vanishes in a column of fire 3 s later.
-- The rollover texts are MM9's level strings, not in the review root: the trace names them.

local CONCUBINE = 9302
local LAUNCH_SECONDS = 0.9
-- Her model has no CastSpell clip: its ranged attack clip (1.5 s) stands in.
local CAST_SECONDS = 1.5

local function setUp(self, s)
    self:setMm9{passive = true, immune = "physical"}
end

-- The concubines in reach at the start (her DeadConcubine counts their deaths: EboraConcubine.scr OnDeath).
local function concubines(self)
    local found = {}

    for _, other in ipairs(self:targets()) do
        if other.monster == CONCUBINE then
            found[#found + 1] = other.index
        end
    end

    return found
end

-- EscapeTheTub / DeadPal: Launch (or Fidget2 for her friend), CastSpell, DitchTheJoint.
local function escape(self, s, why)
    s.escaping = true
    s.step = "launch"
    self:perform{clip = why == "dead_pal" and "fidget2" or "launch",
        seconds = why == "dead_pal" and 3.367 or LAUNCH_SECONDS, fallback = "standing"}
    self:trace("escape " .. why)
end

-- EboraMines FreeAtLast: fidget2 3 s, Taunt 5 s, Rattack1 2 s, the column of fire, gone 3 s later.
local function freeAtLast(self, s, why)
    s.escaping = true
    s.step = "mines_fidget"
    self:perform{clip = "fidget2", seconds = 3, fallback = "standing"}
    self:trace("free_at_last " .. why)
end

return Behavior.define{
    version = 1,
    think_interval = 0.2,

    onStart = function(self, s)
        s.mode = self:placement() == "eboramines.scr" and "mines"
            or self:placement() == "eborabath.scr" and "bath" or "plain"

        if s.mode == "plain" then
            return
        end

        setUp(self, s)
        s.concubines = concubines(self)
        s.dead = 0
        self:trace("mode " .. s.mode .. " concubines " .. #s.concubines)
    end,

    onLoad = function(self, s)
        if s.mode ~= "plain" then
            setUp(self, s)
        end
    end,

    onThink = function(self, s)
        if s.mode ~= "bath" or s.escaping then
            return
        end

        -- OnFoundPlayer: once, Launch and a taunt.
        if not s.found and self:seesParty() then
            s.found = true
            self:perform{clip = "launch", seconds = LAUNCH_SECONDS, fallback = "standing"}
            self:trace("found_player launch text 14")
        end

        -- A concubine's OnDeath sends DeadConcubine.
        for slot, index in pairs(s.concubines) do
            local concubine = self:actor(index)

            if concubine ~= nil and concubine.dead and not s.escaping then
                s.concubines[slot] = nil
                s.dead = s.dead + 1

                if s.dead >= 3 then
                    escape(self, s, "concubines")
                else
                    self:trace("dead_concubine " .. s.dead .. " text " .. (8 + s.dead))
                end
            end
        end
    end,

    onHit = function(self, s, attacker)
        if s.mode == "mines" and not s.escaping then
            freeAtLast(self, s, "hit")
        end
    end,

    onTrigger = function(self, s, message)
        local text = message:lower()

        if s.mode == "mines" and not s.escaping and text == "freeatlast" then
            freeAtLast(self, s, "trigger")
        elseif s.mode == "bath" and not s.escaping and text == "deadpal" then
            escape(self, s, "dead_pal")
        end
    end,

    onPerformDone = function(self, s)
        if s.step == "launch" then
            s.step = "cast"
            self:perform{fallback = "attack_ranged", seconds = CAST_SECONDS}
            self:trace("cast")
        elseif s.step == "cast" then
            s.step = "gone"
            self:effect("mm9:column_of_fire", 1.0, 0.0)
            self:startTimer("leave", 1.0)
            self:trace("column_of_fire")
        elseif s.step == "mines_fidget" then
            s.step = "mines_taunt"
            self:perform{clip = "taunt", seconds = 5, fallback = "standing"}
            self:trace("taunt text 8")
        elseif s.step == "mines_taunt" then
            s.step = "mines_cast"
            self:perform{fallback = "attack_ranged", seconds = 2}
            self:trace("cast")
        elseif s.step == "mines_cast" then
            s.step = "gone"
            self:effect("mm9:column_of_fire", 1.0, 0.0)
            self:startTimer("leave", 3.0)
            self:trace("column_of_fire")
        end
    end,

    onTimer = {
        leave = function(self, s)
            self:leave()
            self:trace("gone")
        end,
    },
}
