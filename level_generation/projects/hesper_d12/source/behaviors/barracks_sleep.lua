-- shortcut: the standing pose holds asleep until the palace's resting animations exist.
return Behavior.define{
    think_interval=0.5,
    onThink=function(self,s)
        if not s.awake then self:perform{clip='rest',seconds=0.6,fallback='standing'} end
    end,
    onDamaged=function(self,s) s.awake=true end,
}
