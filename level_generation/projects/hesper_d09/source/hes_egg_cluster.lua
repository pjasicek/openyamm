local function arm(self, s)
    s.hatched = s.hatched or 0
    if s.hatched < 2 and not self:hasTimer('hatch') then self:startTimer('hatch', 15) end
end
return Behavior.define{
    onStart = arm,
    onLoad = arm,
    onTimer = {hatch = function(self, s)
        if s.hatched < 2 and self:distanceToParty() < 2200 then
            self:summon(10003, 1, 200)
            s.hatched = s.hatched + 1
        end
        arm(self, s)
    end},
}
