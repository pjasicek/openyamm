-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASEMELEE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "basemelee.inc" }

-- BaseMelee.scr
-- Jeff Leggett
-- This script uses baseMelee.inc and doesn't
-- add anything to it.  We just use this
-- script to initialize basemelee.inc and we
-- let it do the work...
script.labels["Main"] = function(ctx)
    -- BASEMELEE.scr:15
    -- This routine is automatically run
    -- at script startup...
    mm9.gosub(script, ctx, "BaseInit") -- BASEMELEE.scr:21
    do return ctx:exit("") end -- BASEMELEE.scr:23
end

return script
