-- Njam the Meddler (MM9 row 261; devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "Phase 5"), by his placement's script:
--
--   njam1000.scr (SpawnNjam.scr's spawns in the 1000 Terrors), and njamtaunt.scr, whose placement the 1000 Terrors
--   converter moves to the spawn markers for SpawnNjam's appearances: Njam1000.inc on his BaseMelee + Range loop.
--   He targets the party at once (Main: Target the player, AddEnemy Player), no physical blow hurts him (Init:
--   CanDamage FALSE) and once his hit points fall below a threshold rolled at start (1 500-4 500 of his 6 600) he
--   vanishes: the test runs in ShouldRunAway, every aggressive tick (0.2 s) while he holds a target; a second after
--   the effect he is gone. A spawned Njam is removed by a load (OnPostMiniSaveLoad Vanish2c).
--   njamchase.scr (Arslegard): stands until the map's Chase trigger or a hit (OnDamage Chase), then hunts the party
--   with the same Njam1000.inc rules (its Init runs Njam1000.inc's).
--   njamfreeze.scr: a cut-scene actor (no AI loop in MM9): passive.
--   njamcameo.scr (Dark Passageway's cameo: SpawnNjamCameo.scr spawns him with it): he wanders (BaseWanderForceStartUp)
--   and never fights; any hit, use or touch sends him away at once (OnDamage, Use and TouchNotify -> Njam1000.inc
--   :Vanish: the effect and Windup10, a second later invisible with the teleport sound). The map's Lua shows him, lets
--   him walk, and after his 10-20 s sends "vanish" (evt.TriggerActor), MM9's SpawnNjamCameo.scr :Vanish2 at that time.
-- Any other placement keeps the plain MM9 loop.

local AGGRESSIVE_TICK = 0.2
local VANISH_SECONDS = 1.0

local function mode(self)
    local script = self:placement()

    if script == "njam1000.scr" or script == "njamtaunt.scr" then
        return "hunt"
    elseif script == "njamchase.scr" then
        return "chase"
    elseif script == "njamfreeze.scr" then
        return "freeze"
    elseif script == "njamcameo.scr" then
        return "cameo"
    end

    return "plain"
end

local function setUp(self, s)
    if s.mode == "freeze" or s.mode == "cameo" then
        self:setMm9{passive = true}
    elseif s.mode == "chase" and not s.chasing then
        self:setMm9{passive = true, immune = "physical"}
    elseif s.mode ~= "plain" then
        self:setMm9{passive = false, immune = "physical"}
    end
end

-- Njam1000.scr Main / NjamChase.scr Chase: the party is his target.
local function hunt(self, s, why)
    s.chasing = true
    setUp(self, s)
    self:setTarget("party")
    self:trace("hunt party " .. why)
end

-- Vanish (Njam1000.inc :Vanish: DoClientFX g_hmyObject, GreaterDemon): the effect now, gone a second later.
local function vanish(self, s, why)
    s.vanishing = true
    self:effect("mm9:GreaterDemon", 1.0, 0.0)
    self:startTimer("vanish", VANISH_SECONDS)
    self:trace("vanish " .. why)
end

-- The cameo's departure (Njam1000.inc :Vanish / SpawnNjamCameo.scr :Vanish2): the effect and Windup10 now, invisible
-- with the teleport sound a second later. A hit cannot kill him first: no damage reaches him once he is going.
local function depart(self, s, why)
    s.vanishing = true
    self:setInvulnerable(true)
    self:effect("mm9:GreaterDemon", 1.0, 0.0)
    self:playSound("magic/windup10.wav")
    self:startTimer("depart", VANISH_SECONDS)
    self:trace("depart " .. why)
end

return Behavior.define{
    version = 1,
    think_interval = AGGRESSIVE_TICK,

    onStart = function(self, s)
        s.mode = mode(self)

        if s.mode == "plain" then
            return
        end

        -- Njam1000.inc Init: getrandomint 1500, 4500, against his 6600 hit points (monster row 9261): kept as that
        -- share of his maximum, so a ruleset that sizes his health (MAW) moves the threshold with it.
        s.threshold = math.floor(self:maxHp() * self:random(1500, 4500) / 6600)
        setUp(self, s)
        self:trace("mode " .. s.mode .. " threshold " .. s.threshold)

        if s.mode == "hunt" then
            hunt(self, s, "start")
        end
    end,

    onLoad = function(self, s)
        if s.mode == "plain" then
            return
        end

        setUp(self, s)

        -- Njam1000.scr: OnPostMiniSaveLoad Vanish2c (a spawned Njam does not survive a load).
        if self:placement() == "njam1000.scr" and not s.vanishing then
            vanish(self, s, "load")
        end
    end,

    onThink = function(self, s)
        if s.mode == "plain" or s.mode == "freeze" or s.mode == "cameo" or s.vanishing or self:target() == nil then
            return
        end

        if self:hp() < s.threshold then
            vanish(self, s, "hp " .. self:hp() .. " below " .. s.threshold)
        end
    end,

    onHit = function(self, s, attacker)
        if s.mode == "chase" and not s.chasing then
            hunt(self, s, "hit")
        elseif s.mode == "cameo" and not s.vanishing then
            depart(self, s, "hit")
        end
    end,

    onTrigger = function(self, s, message)
        if s.mode == "chase" and not s.chasing and message:lower() == "chase" then
            hunt(self, s, "trigger")
        elseif s.mode == "cameo" and not s.vanishing and message:lower() == "vanish" then
            depart(self, s, "trigger")
        end
    end,

    onTimer = {
        vanish = function(self, s)
            self:leave()
        end,
        depart = function(self, s)
            self:playSound("magic/teleport.wav")
            self:leave()
        end,
    },
}
