return Behavior.define{
    version = 1,
    onStart = function(self, s)
        self:setNoFlee(true)
        self:startTimer("fire", 12)
    end,
    onTimer = {
        fire = function(self, s)
            self:say("Burn!")
            self:startTimer("release", 1)
            self:startTimer("fire", 12)
        end,
        release = function(self, s)
            self:castNext{spell = "Fireball", skill = 10, mastery = "master"}
        end,
    },
}
