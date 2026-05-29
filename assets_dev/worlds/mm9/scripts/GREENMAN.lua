-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GREENMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "basewander.inc" }

-- GreenMan.scr
script.labels["OnDamage"] = function(ctx)
    -- GREENMAN.scr:10
    -- can't wince, so don't....
    do return ctx:exit("TRUE") end -- GREENMAN.scr:16
end

script.labels["Main"] = function(ctx)
    -- GREENMAN.scr:19
    mm9.gosub(script, ctx, "BaseWanderInit") -- GREENMAN.scr:22
    ctx:onEvent("OnDamage", "OnDamage") -- GREENMAN.scr:23
    do return ctx:exit("") end -- GREENMAN.scr:25
end

return script
