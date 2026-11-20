return Behavior.define{
    version = 1,
    onStart = function(self, s)
        self:setNoFlee(true)
        self:startTimer("slam", 30)
    end,
    onTimer = {
        slam = function(self, s)
            self:perform{clip = "attack_melee", seconds = 2, fallback = "attack_ranged"}
            self:startTimer("slam", 30)
        end,
    },
    onHealthBelow = {
        [0.4] = function(self, s)
            self:say("The fire answers ME!")
            self:setSpell{spell = "Meteor Shower", skill = 14, mastery = "master", chance = 30}
        end,
    },
}
