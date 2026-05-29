-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BAT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "baserange.inc" }

-- bat.scr
-- Quick/dirty bat implementation..
-- Start off as stone
-- When a player is found, it will start flying after him...
script.labels["LaunchDone"] = function(ctx)
    -- BAT.scr:15
    mm9.gosub(script, ctx, "BaseGoGetHim") -- BAT.scr:18
    do return ctx:exit("TRUE") end -- BAT.scr:19
end

script.labels["FoundPlayer"] = function(ctx)
    -- BAT.scr:22
    mm9.gosub(script, ctx, "InitBase") -- BAT.scr:24
    ctx:self():setTarget(ctx:object("g_hTarget")) -- BAT.scr:26
    ctx:self():launch("LaunchDone", 24) -- BAT.scr:27
    do return ctx:exit("TRUE") end -- BAT.scr:29
end

script.labels["Alert"] = function(ctx)
    -- BAT.scr:32
    do return ctx:exit("FALSE") end -- BAT.scr:34
end

script.labels["Main"] = function(ctx)
    -- BAT.scr:37
    -- traceon
    mm9.gosub(script, ctx, "BaseRangeInit") -- BAT.scr:43
    ctx:onEvent("OnFoundPlayer", "FoundPlayer") -- BAT.scr:45
    ctx:onEvent("OnAlert", "Alert") -- BAT.scr:46
    ctx:self():loopAnimation("Roost", 0) -- BAT.scr:48
    do return ctx:exit("") end -- BAT.scr:51
end

return script
