-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPCBASE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 20, path = "npcBase.inc" }

-- NPCBASE.SCR
-- Jeff Leggett
-- 08/09/2001
-- Behavior:
-- - Wander around using basewander script.  If the USE
-- key is used on us, then this script will be paused.
-- And the RUDE system will take over....
-- - If projectiles have been used near us, or we've been
-- damaged, then we'll run away from the attacker.
-- - Occasionally, we'll look for another NPC to walk over
-- and talk to.
script.labels["Main"] = function(ctx)
    -- NPCBASE.scr:23
    mm9.gosub(script, ctx, "NPCBaseInit") -- NPCBASE.scr:27
    do return ctx:exit("") end -- NPCBASE.scr:28
end

return script
