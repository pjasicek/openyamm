-- D5's first duel. His 6000 HP row is the half he loses here; the map hides his defeated group.
return Behavior.define{
    version = 1,
    think_interval = 0.5,
    onStart = function(self, s) self:setNoFlee(true) end,
    onThink = function(self, s)
        if not s.greeted and self:distanceToParty() < 2200 then
            s.greeted = true    -- his first-sight line is the map's (hes_d05.handlers.lua, QBit 100540)
            self:perform{clip = "fidget", seconds = 3, fallback = "standing"}
            self:startTimer("charge", 8)
        end
    end,
    onTimer = {
        charge = function(self, s)
            -- Flavour only: leave the native ranged AI and its attack cadence uninterrupted.
            self:effect("openyamm:fx/arcane_pulse", 1.5)
            self:startTimer("charge", 8)
        end,
    },
    onHealthBelow = {
        [0.5] = function(self, s) self:say("Ha. You do bite.") end,
        [0.1] = function(self, s)
            self:say("Enough. Not here, in a tower full of servants: come to the ship you came to kill, "
                .. "and I will offer you terms.")
            self:perform{clip = "fidget", seconds = 2, fallback = "standing"}
        end,
    },
    onDeath = function(self, s) self:effect("openyamm:fx/arcane_pulse", 1.5) end,
}
