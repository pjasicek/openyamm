return Behavior.define{
    onStart=function(self,s)
        self:setNoFlee(true); self:startTimer('attack',10)
        if not s.spoken then
            s.spoken=true
            self:say('Lord Xith: Keep your distance, colonists. I will keep mine.')
            self:playSound('vo_xith_sight')      -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
        end
    end,
    onTimer={attack=function(self)
        self:perform{clip='charged_shot',seconds=1,fallback='attack_melee'}
        self:castNext{spell='Lightning Bolt',skill=16,mastery='master'}
        self:startTimer('attack',10)
    end},
    onDeath=function(self) self:say('Ha. Well shot.') end,
}
