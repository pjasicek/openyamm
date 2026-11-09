return Behavior.define{
    onStart=function(self,s)
        self:setNoFlee(true); self:startTimer('attack',6)
        if not s.spoken then
            s.spoken=true
            self:say('Lady Ssekh: Small and soft. I will be quick; it is a kindness.')
            self:playSound('vo_ssekh_sight')      -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
        end
    end,
    onTimer={attack=function(self)
        self:perform{clip='dive',seconds=0.8,fallback='attack_melee'}
        
        self:startTimer('attack',6)
    end},
    onDeath=function(self) self:say('Quick... was the kindness...') end,
}
