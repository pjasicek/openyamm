return Behavior.define{
    onStart=function(self)
        self:setNoFlee(true)
        self:say('Enough. I will do it myself. Court! To me!')
        self:setSpell{spell='Lightning Bolt',skill=20,mastery='master',chance=30}
        self:startTimer('storm',10)
    end,
    onTimer={storm=function(self)
        self:perform{clip='wing_spread',seconds=1.5,fallback='attack_ranged'}
        self:castNext{spell='Lightning Bolt',skill=20,mastery='master'}
        self:startTimer('storm',10)
    end},
    onDeath=function(self) self:effect('openyamm:fx/arcane_pulse',2) end,
}
