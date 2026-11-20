-- One authored script, compiled with a constant stage for each catalogue id.
local stage=CONDUCTOR_STAGE
local duration=({[3]=10,[2]=6,[1]=4})[stage]
local period=({[3]=10,[2]=12,[1]=16})[stage]
local function ward(self)
    self:addWard{id='drawn',radius=500,seconds=duration,visual={color={205,175,255}}}
    self:startTimer(stage==3 and 'ward' or 'warn',stage==3 and period or period-1)
end
return {
    onStart=function(self)
        self:setNoFlee(true)
        self:setSpell{spell='Meteor Shower',skill=14,mastery='master',chance=stage==0 and 45 or 30}
        if stage<3 then
            self:setAiType(stage==0 and 'aggressive' or 'normal')
            self:say("You cut the Crown's own veins!")
        end
        if stage>0 then ward(self)
        else
            self:say('Then I am the last light. Look at me.')
            self:effect('hesper:fx/d16_staff',1,0.8)
            self:startTimer('staff',1)
        end
    end,
    onThink=function(self,s)
        if not s.greeted and self:distanceToParty()<2200 then
            s.greeted=true
            if stage==3 then
                self:say('The Conductor: Every spark in this node is mine. Come, drink of it.')
                self:playSound('vo_conductor_sight')      -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
            end
        end
    end,
    onTimer=function(self,s,id)
        if id=='warn' then
            self:effect('hesper:fx/d16_staff',1,0.8)
            self:playSound('kr_lance_charge')
            self:startTimer('ward',1)
        elseif id=='ward' then ward(self)
        elseif id=='staff' then self:effect('hesper:fx/d16_staff',1,0.8);self:startTimer('staff',1) end
    end,
    onDeath=function(self) self:say('The dark... is cold...') end,
}
