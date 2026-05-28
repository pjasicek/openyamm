-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HATE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basemelee.inc" }

-- Hate.scr
-- timmy
-- Makes things hate things and then runs BaseMelee
script.labels["Main"] = function(ctx)
    -- HATE.scr:13
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("addfriend", "NPC") -- HATE.scr:18
    ctx:command("addfriend", "Player") -- HATE.scr:19
    ctx:command("addenemy", "Horde") -- HATE.scr:20
    mm9.gosub(script, ctx, "BaseInit") -- HATE.scr:22
    do return ctx:exit("") end -- HATE.scr:23
end

return script
