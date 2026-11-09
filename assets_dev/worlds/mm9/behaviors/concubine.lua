-- Ebora's concubines (MM9 row 302, EboraConcubine.scr; devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "Phase 5"): on
-- their BaseMelee loop, but the first sight of the party (OnFoundPlayer) launches them (their Launch clip) before
-- they set up the target and fight (OnLaunchDone). Ebora counts their deaths herself (ebora.lua).

local LAUNCH_SECONDS = 0.9

return Behavior.define{
    version = 1,

    onStart = function(self, s)
        s.bath = self:placement() == "eboraconcubine.scr"
    end,

    onTargetChanged = function(self, s, target)
        if s.bath and not s.launched and target ~= nil and target.kind == "party" then
            s.launched = true
            self:perform{clip = "launch", seconds = LAUNCH_SECONDS, fallback = "standing"}
            self:trace("found_player launch")
        end
    end,
}
