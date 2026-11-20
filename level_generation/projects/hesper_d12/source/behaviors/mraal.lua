return Behavior.define{
    onStart=function(self,s)
        self:setNoFlee(true); self:startTimer('attack',8)
        if not s.spoken then
            s.spoken=true
            self:say('Lord Mraal: Ssekh was always too fast to think. I am not fast.')
            self:playSound('vo_mraal_sight')      -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
        end
    end,
    onTimer={attack=function(self)
        self:perform{clip='cleave',seconds=1.2,fallback='attack_melee'}
        
        self:startTimer('attack',8)
    end},
    onDeath=function(self) self:say('Heavy... going down...') end,
}
