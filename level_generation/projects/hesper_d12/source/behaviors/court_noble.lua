-- shortcut: Lightning Bolt is the design's indoor Meteor Shower substitute.
return Behavior.define{onStart=function(self)
    self:setNoFlee(true)
    self:setSpell{spell='Lightning Bolt',skill=12,mastery='master',chance=30}
end}
