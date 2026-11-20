return Behavior.define{
    onStart=function(self)
        self:setNoFlee(true)
        -- His first-sight line is the map's (hes_d12.handlers.lua handler 158); the old entry speech is retired.
        self:addWard{id='throne',radius=900,seconds=3600,visual={color={0.7,0.4,1},intensity=1,rim=2,noise=0.2}}
        self:setSpell{spell='Lightning Bolt',skill=20,mastery='master',chance=40}
    end,
}
