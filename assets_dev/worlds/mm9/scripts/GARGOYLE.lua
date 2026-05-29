-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GARGOYLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "aiglobals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "base.inc" }

-- gargoyle.scr
-- Quick/dirty gargoyle implementation..
-- Start off as stone
-- When a player is found, it will start flying after him...
script.labels["LaunchDone"] = function(ctx)
    -- GARGOYLE.scr:15
    mm9.gosub(script, ctx, "BaseGoGetHim") -- GARGOYLE.scr:18
    do return ctx:exit("TRUE") end -- GARGOYLE.scr:20
end

script.labels["StandupDone"] = function(ctx)
    -- GARGOYLE.scr:23
    mm9.gosub(script, ctx, "InitBase") -- GARGOYLE.scr:25
    ctx:self():setTarget(ctx:object("g_hTarget")) -- GARGOYLE.scr:27
    ctx:self():launch("LaunchDone", 24) -- GARGOYLE.scr:28
    do return ctx:exit("TRUE") end -- GARGOYLE.scr:30
end

script.labels["FoundPlayer"] = function(ctx)
    -- GARGOYLE.scr:33
    ctx:getParam(0, "g_hTarget") -- GARGOYLE.scr:35
    ctx:self():setTarget(ctx:object("g_hTarget")) -- GARGOYLE.scr:36
    ctx:self():playAnimation("StandUp", "StandupDone") -- GARGOYLE.scr:38
    do return ctx:exit("TRUE") end -- GARGOYLE.scr:40
end

script.labels["Alert"] = function(ctx)
    -- GARGOYLE.scr:43
    do return ctx:exit("FALSE") end -- GARGOYLE.scr:45
end

script.labels["Main"] = function(ctx)
    -- GARGOYLE.scr:48
    -- traceon
    mm9.gosub(script, ctx, "InitBase") -- GARGOYLE.scr:54
    ctx:onEvent("OnFoundPlayer", "FoundPlayer") -- GARGOYLE.scr:56
    ctx:onEvent("OnAlert", "Alert") -- GARGOYLE.scr:57
    ctx:self():loopAnimation("STATIC_MODEL", 0) -- GARGOYLE.scr:59
    do return ctx:exit("") end -- GARGOYLE.scr:62
end

return script
