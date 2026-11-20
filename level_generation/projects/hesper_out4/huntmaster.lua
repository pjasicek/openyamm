-- Huntmaster Vreth (10147), the Blooding Ring's master (design/kreegan_world/HARROWERS.md, "The fight"). His charge,
-- afterimage blink and kindling (the frenzy, with its roar) are the world's modifiers.yml; this script says his lines.
-- His lines are P4's
-- (design/kreegan_world/quests/dialogue/CROWN.md, "The Blooding Ring"). build_out4.py copies it into the map's
-- runtime tree; the stage installs it as worlds/hesper/behaviors/bosses/huntmaster.lua.
return Behavior.define{
    version = 1,
    onStart = function(self, s)
        self:setNoFlee(true)
    end,
    onHealthBelow = {
        [0.5] = function(self, s)
            self:say('Huntmaster Vreth: "Yes. YES! Now you are worth the hunt!"')
        end,
    },
    onDeath = function(self, s)
        if s.lastWords then return end
        s.lastWords = true
        self:say('Huntmaster Vreth: A good hunt... a good... hunt.')
        self:playSound('vo_vreth_death')      -- voiced (design/kreegan_world/audio/BOSS_LINES.md)
    end,
}
