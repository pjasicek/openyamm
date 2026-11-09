return Behavior.define{
    version = 1,
    onStart = function(self, s)
        self:setNoFlee(true)
        self:startTimer("prod", 15)
    end,
    onHealthBelow = {
        [0.3] = function(self, s)
            self:say("Hold them! Hold them off me!")
            self:setNoFlee(false)
            self:setAiType("wimp")
            self:startTimer("land", 8)
        end,
    },
    onTimer = {
        prod = function(self, s)
            self:say("Forward, meat!")
            self:perform{clip="attack_melee", seconds=1}
            self:startTimer("prod", 15)
        end,
        land = function(self, s)
            self:setAiType(nil)
            self:setNoFlee(true)
        end,
    },
}
