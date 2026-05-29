-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP3FIREELEMENTAL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "base.inc" }

-- DP3fireelemental.scr
-- Timmy
-- This script makes a fire elemental throw a switch
-- Parameters:
script.labels["Nav1"] = function(ctx)
    -- DP3FIREELEMENTAL.scr:23
    if ctx:condition("Aware==True") then -- DP3FIREELEMENTAL.scr:26
        do return mm9.gotoLabel(script, ctx, "Attack") end -- DP3FIREELEMENTAL.scr:27
        do return ctx:exit("") end -- DP3FIREELEMENTAL.scr:28
    end -- DP3FIREELEMENTAL.scr:29
    ctx:state().Aware = true -- DP3FIREELEMENTAL.scr:32
    ctx:object("Trigger0"):trigger("off") -- DP3FIREELEMENTAL.scr:33-34
    ctx:state().g_hobject = ctx:objectOrNil("Switch2") -- DP3FIREELEMENTAL.scr:35
    ctx:self():runTo(ctx:object("g_hobject"), 32, "Fidget1") -- DP3FIREELEMENTAL.scr:36
    do return ctx:exit("") end -- DP3FIREELEMENTAL.scr:37
end

script.labels["Fidget1"] = function(ctx)
    -- DP3FIREELEMENTAL.scr:41
    ctx:trigger("g_hobject", "use") -- DP3FIREELEMENTAL.scr:45
    ctx:wait(3, 3, "OnAware") -- DP3FIREELEMENTAL.scr:46
    do return ctx:exit("") end -- DP3FIREELEMENTAL.scr:48
end

script.labels["OnAware"] = function(ctx)
    -- DP3FIREELEMENTAL.scr:51
    ctx:state().g_hobject = ctx:objectOrNil("Trigger0") -- DP3FIREELEMENTAL.scr:56
    ctx:self():faceObject(ctx:object("g_hobject"), 100, "Attack") -- DP3FIREELEMENTAL.scr:57
    do return ctx:exit("") end -- DP3FIREELEMENTAL.scr:58
end

script.labels["Attack"] = function(ctx)
    -- DP3FIREELEMENTAL.scr:61
    do return mm9.gotoLabel(script, ctx, "InitBase") end -- DP3FIREELEMENTAL.scr:64
    do return ctx:exit("") end -- DP3FIREELEMENTAL.scr:65
end

script.labels["Stuck"] = function(ctx)
    -- DP3FIREELEMENTAL.scr:67
    do return mm9.gotoLabel(script, ctx, "Nav1") end -- DP3FIREELEMENTAL.scr:71
    do return ctx:exit("") end -- DP3FIREELEMENTAL.scr:72
end

script.labels["Main"] = function(ctx)
    -- DP3FIREELEMENTAL.scr:75
    -- TRACEON
    ctx:onEvent("OnStuck", "Stuck") -- DP3FIREELEMENTAL.scr:81
    ctx:addTrigger("Aware", "OnAware") -- DP3FIREELEMENTAL.scr:82
    ctx:addTrigger("Start", "Nav1") -- DP3FIREELEMENTAL.scr:83
    ctx:onEvent("OnDamage", "Nav1") -- DP3FIREELEMENTAL.scr:84
    do return ctx:exit("") end -- DP3FIREELEMENTAL.scr:85
end

return script
