return Behavior.define{
    think_interval=0.5,
    onStart=function(self) self:setNoFlee(true) end,
    onThink=function(self,s)
        if not s.spoken and self:distanceToParty()<1100 then
            s.spoken=true
            self:say('The Gatekeeper: Vermin in the cellar. Lancers, sweep it out.')
            self:playSound('vo_gatekeeper_sight')      -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
        end
    end,
    onHealthBelow={[0.5]=function(self)
        self:say('Sentinels! Burn the floor round them!')
        self:addWard{id='gatekeeper',radius=400,seconds=8,visual={color={0.7,0.4,1},intensity=1,rim=2,noise=0.2}}
    end},
    onDeath=function(self) self:say('The gate... opens... from inside. The Hierarch... will...') end,
}
