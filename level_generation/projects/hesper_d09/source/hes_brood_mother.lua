local function arm(self)
    self:setNoFlee(true)
    if not self:hasTimer('spit') then self:startTimer('spit', 6) end
end
return Behavior.define{
    onStart = arm,
    onLoad = arm,
    onTimer = {spit = function(self)
        if self:distanceToParty() < 4000 then
            self:perform{clip = 'acid_swell', seconds = 1.2, fallback = 'attack_ranged',
                         effect = 'hesper:fx/projectile/crawler_acid'}
        end
        self:startTimer('spit', 6)
    end},
    -- shortcut: castNext controls spells, not attack1; the native acid projectile resumes after the swell.
    onHealthBelow = {[0.5] = function(self) self:say('The hive shakes with the Mother\'s voiceless scream.') end},
}
