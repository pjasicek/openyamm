-- Yanmir (MM9 row 206, YanmirBase.scr; devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "Phase 5"), on his BaseCrawl +
-- Range loop. No blow hurts him (Reset: CanDamage FALSE, TELP 1.3) and he answers no alerts (OnAlert). Awake (the
-- map's Squish trigger wakes his dormant start: Begin), he hunts bugs: 3 s after he has no target, then every
-- 0.5-2 s, one of the Ice Lobbercicles within 500 LT, picked at random, that he sees. He gives up on a bug after 15 s
-- without an attack (on the party after 45 s: MAX_CHASE_TIME) or after his fourth attack at it, and wipes his shoe
-- 0.2 s after he squashed one. The trap, his fall, the door kicks and his reward are the map's (yanmirsfort.lua).

local LT = 2.56
local BUG = 9105
local BUG_DISTANCE = 500 * LT
local LOOK_START_SECONDS = 3
local PLAYER_CHASE_SECONDS = 45
local BUG_CHASE_SECONDS = 15
local MAX_BUG_ATTEMPTS = 3
local WIPE_DELAY_SECONDS = 0.2
local WIPE_SECONDS = 3.5

local function setUp(self, s)
    self:setMm9{ignores_calls = true, immune = "physical",
        chase_limit = s.targetIsParty and PLAYER_CHASE_SECONDS or BUG_CHASE_SECONDS}
end

local function name(target)
    return target.kind == "party" and "party" or ("actor:" .. target.index)
end

-- LookForBugsStart.
local function lookForBugs(self, s)
    self:startTimer("bugs", LOOK_START_SECONDS)
end

return Behavior.define{
    version = 1,

    onStart = function(self, s)
        setUp(self, s)
        lookForBugs(self, s)
    end,

    onLoad = function(self, s)
        setUp(self, s)
    end,

    -- SetupTarget: his chase limit by whom he holds; ClearTarget: the bug search again.
    onTargetChanged = function(self, s, target)
        if target ~= nil then
            s.targetIsParty = target.kind == "party"
            s.target = {kind = target.kind, index = target.index}
            s.attempts = 0
            self:stopTimer("bugs")
            setUp(self, s)
            self:trace("target " .. name(target) .. " chase_limit "
                .. (s.targetIsParty and PLAYER_CHASE_SECONDS or BUG_CHASE_SECONDS))
            return
        end

        -- OnTargetDead: his own kill (a bug he squashed: it lies dead) earns the wipe.
        local previous = s.target
        s.target = nil
        lookForBugs(self, s)

        if previous ~= nil and previous.kind == "actor" then
            local bug = self:actor(previous.index)

            if bug ~= nil and bug.dead then
                self:startTimer("wipe", WIPE_DELAY_SECONDS)
            end
        end
    end,

    -- AttackDone: a fourth attack at a bug gives up on it.
    onAttackDone = function(self, s)
        if s.target == nil or s.targetIsParty then
            return
        end

        s.attempts = (s.attempts or 0) + 1

        if s.attempts > MAX_BUG_ATTEMPTS then
            self:setTarget(nil)
            self:trace("give_up bug attempts " .. s.attempts)
        end
    end,

    onTimer = {
        -- LookForBugsTick: again in 0.5-2 s; with no target, a random visible Ice Lobbercicle within 500 LT.
        bugs = function(self, s)
            self:startTimer("bugs", 0.5 + 1.5 * self:random())

            if self:dormant() or self:target() ~= nil or self:isPerforming() then
                return
            end

            local bugs = {}

            for _, other in ipairs(self:targets(BUG_DISTANCE)) do
                if other.monster == BUG then
                    bugs[#bugs + 1] = other
                end
            end

            if #bugs == 0 then
                return
            end

            local bug = bugs[self:random(1, #bugs)]

            if bug.clear then
                self:setTarget(bug.index)
                self:trace("bug " .. name(bug) .. " of " .. #bugs)
            end
        end,

        -- Wipe: his Wipe clip, then he walks on.
        wipe = function(self, s)
            self:perform{clip = "wipe", seconds = WIPE_SECONDS, fallback = "standing"}
            self:trace("wipe")
        end,
    },
}
