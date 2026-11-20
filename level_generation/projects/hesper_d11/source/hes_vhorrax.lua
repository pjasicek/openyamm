-- Build emits the two forms with one constant changed; the map arms only the chosen form.
local honour = HONOUR
local function arm(self,s)
    self:setNoFlee(true)
    s.adds = s.adds or 0
    if not self:hasTimer('lunge') then self:startTimer('lunge',honour and 6 or 8) end
    if not honour and s.adds < 4 and not self:hasTimer('adds') then self:startTimer('adds',30) end
end
return Behavior.define{
    version = 1,
    onStart = arm, onLoad = arm,
    onTimer = {
        lunge = function(self,s)
            self:perform{clip='fidget',seconds=1.5,fallback='standing',effect='openyamm:fx/arcane_pulse',sound='d11_lunge'}
            self:startTimer('release',1.5)
            self:startTimer('lunge',honour and 6 or 8)
        end,
        release = function(self,s)
            -- shortcut: the supported castNext attack stands in for a physical dash until native lunges exist.
            self:castNext{spell='Incinerate',skill=12,mastery='master'}
        end,
        adds = function(self,s)
            if s.adds >= 4 then return end
            self:say('Overseers!')
            self:summon(10031,1,600)
            s.adds=s.adds+1
            if s.adds < 4 then self:startTimer('adds',30) end
        end,
    },
    onHealthBelow = {
        [0.75] = function(self,s) self:say('Ha! Again!') end,
        [0.5] = function(self,s) self:say("Your makers' tools in your hands. They serve you well. Ours served us better, once.") end,
        [0.25] = function(self,s) self:say(honour and 'If I fall, colonists, say that I fell standing.'
            or 'Swarm them! What are you waiting for?') end,
    },
}
