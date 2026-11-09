-- MM9's summoners (devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "Phase 5"), by their placement's script; the
-- placement's summon class and points come from the scene's mm9_ai (the converters resolve the spawn locations):
--
--   summoner.scr (the Lich Lab's Power Lich; SpawnMgr.scr, SpawnLoc.scr): fights on BaseMelee. Its map trigger
--   `startup` summons a minion at every point (sparklies and blue fire there), then acts as when a minion died: the
--   spawn manager's `trigger` (OnMinionDied) focuses a random point (GetRandomInt first, last) with the effects,
--   plays RAttack1 (StopMoving), and the manager spawns the next minion there. Its death shuts the manager off.
--   isle_summoner.scr (Isle of Ashes): on its `spawn` trigger it plays hAttack1 and spawns its class at its point; at
--   its sixth trigger it removes the trigger (quirk: nCounter >= 5 is tested before the count, so six come).
-- The spawn manager is folded in: the script counts its own minions (self:actor) and spawns the replacement of each
-- one that died. Its totals (SpawnMgr's own limits) are map data the review root does not carry: no cap here.

-- MM9 class names a summoner may name, to rows (numbers are taken as rows).
local CLASSES = {
    Skeletoid = 9183,
    Shadow = 9138,
    Apparition = 9139,
    Specter = 9140,
}
local RATTACK1_SECONDS = 1.2
local HATTACK1_SECONDS = 0.7
local ISLE_SPAWN_LAST = 5

local function classRow(summonClass)
    return tonumber(summonClass) or CLASSES[summonClass]
end

local function spawnAt(self, s, point)
    self:summonAt(s.row, point[1], point[2], point[3])
end

-- The summoner's look at a point (DoClientFX LISTOBJECT, SPELL_SPARKLIES and SPELL_BLUEFIRE).
local function sparkle(self, point)
    self:effectAt("mm9:sparklies", point[1], point[2], point[3])
    self:effectAt("mm9:fireblue", point[1], point[2], point[3])
    self:trace("focus " .. point[1] .. " " .. point[2] .. " " .. point[3])
end

-- OnMinionDied: a random point gets the focus and the next minion; RAttack1 meanwhile.
local function minionDied(self, s)
    local points = self:summonPoints()
    local first = s.first or 1
    local last = math.min(s.last or #points, #points)
    local point = points[self:random(first, last)]
    sparkle(self, point)
    self:perform{fallback = "attack_ranged", seconds = RATTACK1_SECONDS}
    return point
end

return Behavior.define{
    version = 1,
    think_interval = 0.5,

    onStart = function(self, s)
        local script, params, summonClass = self:placement()
        s.mode = script == "summoner.scr" and "summoner" or script == "isle_summoner.scr" and "isle" or "plain"
        s.row = classRow(summonClass)
        s.minions = {}
        s.spawned = 0

        -- Summoner.scr: p0 the spawn locations' name, p1 the first index, p2 the last.
        local _, p1, p2 = params:match("^(%S+)%s+(%d+)%s+(%d+)")

        if p1 ~= nil then
            s.first = tonumber(p1) + 1
            s.last = tonumber(p2) + 1
        end

        if s.mode ~= "plain" then
            self:trace("mode " .. s.mode .. " class " .. tostring(s.row) .. " points " .. #self:summonPoints())
        end
    end,

    onTrigger = function(self, s, message)
        local points = self:summonPoints()
        local text = message:lower()

        if s.row == nil or #points == 0 or s.stopped then
            return
        end

        if s.mode == "summoner" and text == "startup" and not s.started then
            -- SummonStarters: every point, then OnMinionDied.
            s.started = true

            for _, point in ipairs(points) do
                sparkle(self, point)
                spawnAt(self, s, point)
            end

            spawnAt(self, s, minionDied(self, s))
            self:trace("startup " .. (#points + 1))
        elseif s.mode == "isle" and text == "spawn" then
            -- SpawnCreature: the counter is tested before it counts.
            if s.spawned >= ISLE_SPAWN_LAST then
                s.stopped = true
            end

            s.spawned = s.spawned + 1
            self:perform{fallback = "attack_melee", seconds = HATTACK1_SECONDS}
            spawnAt(self, s, points[1])
            self:trace("spawn " .. s.spawned)
        end
    end,

    -- The spawn manager's minions: those of its class that appeared after the startup; each one that dies brings the
    -- next (SpawnMgr's `trigger` to the summoner, OnMinionDied).
    onThink = function(self, s)
        if s.mode ~= "summoner" or not s.started then
            return
        end

        for _, other in ipairs(self:targets()) do
            if other.monster == s.row then
                s.minions[tostring(other.index)] = true
            end
        end

        for index, _ in pairs(s.minions) do
            local minion = self:actor(tonumber(index))

            if minion ~= nil and minion.dead then
                s.minions[index] = nil
                local point = minionDied(self, s)
                spawnAt(self, s, point)
                self:trace("minion_died " .. index)
            end
        end
    end,

    -- OnDeath: the spawn manager is switched off.
    onDeath = function(self, s)
        s.stopped = true
    end,
}
