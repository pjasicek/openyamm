return {
    onStart=function(self)
        self:setNoFlee(true)
        self:say('COUPLINGS SEVERED. DEFENCE MODE.')
        self:startTimer('sweep',12)
    end,
    onTimer={
        sweep=function(self)
            self:perform{clip='sweep',seconds=1.5,fallback='attack_ranged'}
            self:startTimer('shot',1.5)
            self:startTimer('sweep',12)
        end,
        shot=function(self) self:castNext{spell='Incinerate',skill=15,mastery='master'} end,
    },
    onHealthBelow={
        [0.35]=function(self)
            self:say('OVERHEAT. OVERHEAT.')
            self:effect('hesper:fx/d07_steam',1,.5)
            self:setAiType('aggressive')
            self:setSpell{spell='Incinerate',skill=15,mastery='master',chance=50}
        end,
    },
    onDeath=function(self) self:say('Node... east... unguarded...') end,
}
