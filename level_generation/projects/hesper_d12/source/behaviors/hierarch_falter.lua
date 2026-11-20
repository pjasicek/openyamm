return Behavior.define{
    onStart=function(self)
        self:setNoFlee(true); self:setAiType('aggressive')
        self:say('Sing! Sing, you broken thing! SING!')
        self:setSpell{spell='Lightning Bolt',skill=20,mastery='master',chance=30}
    end,
    onDeath=function(self,s)
        if s.lastWords then return end
        s.lastWords=true
        self:say('The Hierarch: I was ... the one in the Voice ...')
        self:playSound('vo_hierarch_death')      -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
    end,
}
