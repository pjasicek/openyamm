return {
    onStart=function(self)
        self:setNoFlee(true)
        self:setSpell{spell='Incinerate',skill=15,mastery='master',chance=20}
    end,
    onThink=function(self,s)
        if not s.greeted and self:distanceToParty()<2200 then
            s.greeted=true; self:say("The Coil Keeper: You walk on the Crown's coil. Stand very still.")
            self:playSound('vo_coil_keeper_sight')      -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
        end
    end,
    onHealthBelow={
        [0.6]=function(self)
            self:say('THE COIL ANSWERS!')
            self:perform{clip='cast',seconds=1.5,fallback='attack_ranged'}
            self:startTimer('aggressive',1.5)
        end,
        [0.25]=function(self)
            self:say('Cold... the coil is cold!')
            self:addWard{id='coil',radius=400,seconds=8,visual={color={170,210,255}}}
        end,
    },
    onTimer=function(self,s,id) if id=='aggressive' then self:setAiType('aggressive') end end,
    onDeath=function(self) self:say('The Hierarch... will hear... the west go dark.') end,
}
