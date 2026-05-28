-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BASESWIM.inc"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "baseCrawl.inc" }

-- BaseSwim.Inc
-- Jeff Leggett
-- 11/07/2001
-- Base script for monsters that SWIM...
script.labels["LocalShouldRunAway"] = function(ctx)
    -- BASESWIM.inc:14
    ctx:command("g_btemp", "= FALSE") -- BASESWIM.inc:16
    ctx:command("getstat", "g_hObject,IsInWater,g_bTemp") -- BASESWIM.inc:18
    if ctx:condition("g_bTemp==FALSE") then -- BASESWIM.inc:20
        ctx:command("g_btemp", "= TRUE") -- BASESWIM.inc:21
        do return ctx:exit("") end -- BASESWIM.inc:22
    end -- BASESWIM.inc:23
    ctx:command("g_btemp", "= FALSE") -- BASESWIM.inc:25
    do return ctx:exit("") end -- BASESWIM.inc:27
end

script.labels["ShouldRunAway"] = function(ctx)
    -- BASESWIM.inc:30
    -- Set g_hObject to the object you're asking about
    -- g_bTemp will be set to TRUE or FALSE
    mm9.gosub(script, ctx, "LocalShouldRunAway") -- BASESWIM.inc:36
    if ctx:condition("g_bTemp==TRUE") then -- BASESWIM.inc:37
        do return ctx:exit("") end -- BASESWIM.inc:38
    end -- BASESWIM.inc:39
    mm9.gosub(script, ctx, "ShouldRunAway") -- BASESWIM.inc:41
    do return ctx:exit("") end -- BASESWIM.inc:43
end

script.labels["BaseShouldRun"] = function(ctx)
    -- BASESWIM.inc:46
    mm9.gosub(script, ctx, "LocalShouldRunAway") -- BASESWIM.inc:49
    if ctx:condition("g_bTemp==TRUE") then -- BASESWIM.inc:50
        do return ctx:exit("") end -- BASESWIM.inc:51
    end -- BASESWIM.inc:52
    mm9.gosub(script, ctx, "BaseShouldRun") -- BASESWIM.inc:54
    do return ctx:exit("") end -- BASESWIM.inc:56
end

script.labels["BaseSwimStartup"] = function(ctx)
    -- BASESWIM.inc:59
    ctx:command("setidle", "") -- BASESWIM.inc:61
    do return ctx:exit("") end -- BASESWIM.inc:62
end

script.labels["BaseSwimInit"] = function(ctx)
    -- BASESWIM.inc:65
    ctx:command("wait", "29,0.1,BaseSwimStartup") -- BASESWIM.inc:67
    mm9.gosub(script, ctx, "BaseCrawlInit") -- BASESWIM.inc:68
    do return ctx:exit("") end -- BASESWIM.inc:69
end

return script
