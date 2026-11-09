-- The hatchery's egg clusters (BROOD_SPIRES.md section 7, group 10): the egg fields' hatching (D9's hes_egg_cluster)
-- with the hatchery's parameters, the hatchery's waves: every 10 s while the party is within 2 200, one Hatchling
-- (10003) within 300, at most four, each with the hatching sound (egg_hatch); then spent. Destroying the cluster stops it
-- at once.
local function arm(self, s)
    s.hatched = s.hatched or 0
    if s.hatched < 4 and not self:hasTimer('hatch') then self:startTimer('hatch', 10) end
end
return Behavior.define{
    onStart = arm,
    onLoad = arm,
    onTimer = {hatch = function(self, s)
        if s.hatched < 4 and self:distanceToParty() < 2200 then
            self:playSound('egg_hatch')
            self:summon(10003, 1, 300)
            s.hatched = s.hatched + 1
        end
        arm(self, s)
    end},
}
