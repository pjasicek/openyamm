-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FLYRANGE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "FlyRange.inc" }

-- FlyRange.scr
-- Jeff Leggett
-- 10/22/2001
-- Base script for creatures that stay in the air and attack and
-- shoot!
script.labels["Init"] = function(ctx)
    -- FLYRANGE.scr:14
    ctx:self():setIdle() -- FLYRANGE.scr:17
    do return ctx:exit("") end -- FLYRANGE.scr:19
end

script.labels["Main"] = function(ctx)
    -- FLYRANGE.scr:22
    -- This routine is automatically run
    -- at script startup...
    mm9.gosub(script, ctx, "FlyRangeInit") -- FLYRANGE.scr:27
    ctx:wait(30, 0.1, "Init") -- FLYRANGE.scr:29
    do return ctx:exit("") end -- FLYRANGE.scr:31
end

return script
