-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WYVERNGROUND.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "base.inc" }

-- Wyvernground.scr
-- Quick-and-dirty script for wyvern...
script.labels["LaunchDone"] = function(ctx)
    -- WYVERNGROUND.scr:13
    ctx:command("runscript", "wyvernair.scr") -- WYVERNGROUND.scr:16
    do return ctx:exit("TRUE") end -- WYVERNGROUND.scr:18
end

script.labels["TimeToFly"] = function(ctx)
    -- WYVERNGROUND.scr:21
    ctx:command("launch", "LaunchDone, 200") -- WYVERNGROUND.scr:24
    do return ctx:exit("TRUE") end -- WYVERNGROUND.scr:26
end

script.labels["DoNothing"] = function(ctx)
    -- WYVERNGROUND.scr:29
    do return ctx:exit("FALSE") end -- WYVERNGROUND.scr:31
end

script.labels["DamageDone"] = function(ctx)
    -- WYVERNGROUND.scr:34
    ctx:command("isonground", "g_bTemp") -- WYVERNGROUND.scr:37
    if ctx:condition("g_bTemp==TRUE") then -- WYVERNGROUND.scr:39
        ctx:command("launch", "BaseGoGetHim, 160") -- WYVERNGROUND.scr:40
        do return ctx:exit("TRUE") end -- WYVERNGROUND.scr:41
    end -- WYVERNGROUND.scr:42
    mm9.gosub(script, ctx, "BaseDamageDone") -- WYVERNGROUND.scr:44
    do return ctx:exit("") end -- WYVERNGROUND.scr:46
end

script.labels["Main"] = function(ctx)
    -- WYVERNGROUND.scr:49
    mm9.gosub(script, ctx, "InitBase") -- WYVERNGROUND.scr:52
    ctx:command("onlosttarget", "TimeToFly") -- WYVERNGROUND.scr:53
    ctx:command("onstuckdone", "TimeToFly") -- WYVERNGROUND.scr:54
    ctx:command("ondamagedone", "DamageDone") -- WYVERNGROUND.scr:55
    ctx:command("setidle", "") -- WYVERNGROUND.scr:57
    do return ctx:exit("") end -- WYVERNGROUND.scr:59
end

return script
