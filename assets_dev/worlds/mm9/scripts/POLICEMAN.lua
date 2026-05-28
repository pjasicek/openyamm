-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "POLICEMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 19, path = "PoliceMan.Inc" }

-- PoliceMan.Scr
-- Jeff Leggett
-- 08/22/2001
-- Behavior
-- - Don't attack anyone unless someone calls for help
-- - If we get a call for help, if we have a path to
-- the target, then we'll go after it. Otherwise, we
-- won't...
-- - Just run the wander script until someone needs us.
-- (or attacks us!)
script.labels["Main"] = function(ctx)
    -- POLICEMAN.scr:22
    mm9.gosub(script, ctx, "PoliceManInit") -- POLICEMAN.scr:25
    do return ctx:exit("") end -- POLICEMAN.scr:28
end

return script
