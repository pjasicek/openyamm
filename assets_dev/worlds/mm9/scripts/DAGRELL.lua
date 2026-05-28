-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DAGRELL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "basemelee.inc" }

-- dagrell.scr
-- Jeff Leggett
-- For now, just a simple crawRange
-- If time permits, I'll make him more
-- interesting....
script.labels["SpeedThrottleStart"] = function(ctx)
    -- DAGRELL.scr:16
    -- Don't speed throttle the Dagrell
    -- Looks funny....
    do return ctx:exit("") end -- DAGRELL.scr:22
end

script.labels["Main"] = function(ctx)
    -- DAGRELL.scr:25
    -- This routine is automatically run
    -- at script startup...
    mm9.gosub(script, ctx, "BaseInit") -- DAGRELL.scr:31
    do return ctx:exit("") end -- DAGRELL.scr:33
end

return script
