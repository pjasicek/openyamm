-- The Harvester (boss 10104, the Great Pit's floor; THE_SCOUR.md section 7, "Set piece: the Harvester (M8)").
-- One loop of about 40 s, no phase change: it grinds for 32 s behind a projectile ward from every side (the built
-- stand-in for its armoured front: shoot it while it digs, melee it any time and take the spray) and sprays slag on
-- a party within 900 every 6 s; then for 8 s it stops, drives the drill into the floor (the `dig` clip) with its heat
-- vents open: the ward drops and it cannot spray. Its post (leash 2 400) and 40 degrees a second of traverse are its
-- monster tactics (hesper_stage/monsters.yml); the Energy Core is its carried item (the map's load event).
local WARD = {id = "front", radius = 700, visual = {color = {1.0, 0.55, 0.2}, intensity = 0.8, rim = 3, noise = 0.4}}

local function grind(self, s)
    s.digging = false
    self:addWard(WARD)
    self:startTimer("dig", 32)
end

return Behavior.define{
    version = 1,
    onStart = function(self, s)
        self:setNoFlee(true)
        grind(self, s)
        self:startTimer("spray", 6)
    end,
    onLoad = function(self, s)
        if not self:hasTimer("dig") and not self:hasTimer("grind") then grind(self, s) end
        if not self:hasTimer("spray") then self:startTimer("spray", 6) end
    end,
    onTimer = {
        dig = function(self, s)
            s.digging = true
            self:removeWard("front")
            self:say("The Harvester's drill bites into the floor; its heat vents gape open.")
            self:perform{clip = "dig", seconds = 8, fallback = "standing"}
            self:startTimer("grind", 8)
        end,
        grind = function(self, s)
            grind(self, s)
        end,
        spray = function(self, s)
            if not s.digging and self:distanceToParty() <= 900 then
                self:castNext{spell = "Fireball", skill = 10, mastery = "master"}
            end
            self:startTimer("spray", 6)
        end,
    },
}
