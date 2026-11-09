-- The Custodian (10100), the Ancient maintenance mech holding D1's Drone Control: its one canned announcement in the
-- Starport's own voice, once, when the party comes within about 1 600 (design/kreegan_world/audio/BOSS_LINES.md).
-- The monster's default behaviour (hesper_d01/behaviors.yml); build_d01.py copies it into the map's runtime tree and
-- the stage installs it as worlds/hesper/behaviors/bosses/custodian.lua. It leaves the native AI alone.
return Behavior.define{
    version = 1,
    think_interval = 0.5,
    onThink = function(self, s)
        if not s.announced and self:distanceToParty() < 1600 then
            s.announced = true
            self:say('The Custodian: DRONE CONTROL IS CLOSED. PLEASE LEAVE THE AREA.')
            self:playSound('vo_custodian_sight')
        end
    end,
}
