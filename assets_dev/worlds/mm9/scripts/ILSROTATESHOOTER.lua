-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSROTATESHOOTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "book.scr" }

-- rotateshooter.scr
-- timmy
-- randomly rotates shooter
script.labels["Parameters"] = function(ctx)
    -- ILSROTATESHOOTER.scr:18
end

-- P0 wait time B/T shots
-- P1 minimum random int range
-- P0 maximum random int range
script.labels["OnRun"] = function(ctx)
    -- ILSROTATESHOOTER.scr:24
    if ctx:condition("stop!=true") then -- ILSROTATESHOOTER.scr:29
        ctx:command("getmyhandle", ", g_hobject") -- ILSROTATESHOOTER.scr:31
        ctx:trigger("g_hobject", "on") -- ILSROTATESHOOTER.scr:32
        ctx:command("getrandomint", "Param1, Param2, g_ntemp") -- ILSROTATESHOOTER.scr:33
        ctx:command("rotate", "0, 1, 0, g_ntemp, 0,") -- ILSROTATESHOOTER.scr:34
        do return mm9.gotoLabel(script, ctx, "wait") end -- ILSROTATESHOOTER.scr:35
    end -- ILSROTATESHOOTER.scr:36
    ctx:trigger("g_hobject", "off") -- ILSROTATESHOOTER.scr:38
    do return ctx:exit("") end -- ILSROTATESHOOTER.scr:39
end

script.labels["wait"] = function(ctx)
    -- ILSROTATESHOOTER.scr:44
    ctx:command("wait", "param0, Onrun") -- ILSROTATESHOOTER.scr:48
    do return ctx:exit("") end -- ILSROTATESHOOTER.scr:50
end

script.labels["Onstart"] = function(ctx)
    -- ILSROTATESHOOTER.scr:54
    ctx:command("set", "stop, false") -- ILSROTATESHOOTER.scr:59
    do return mm9.gotoLabel(script, ctx, "Onrun") end -- ILSROTATESHOOTER.scr:61
    do return ctx:exit("") end -- ILSROTATESHOOTER.scr:62
end

script.labels["Onstop"] = function(ctx)
    -- ILSROTATESHOOTER.scr:66
    ctx:command("set", "stop, true") -- ILSROTATESHOOTER.scr:69
    do return ctx:exit("") end -- ILSROTATESHOOTER.scr:71
end

script.labels["Main"] = function(ctx)
    -- ILSROTATESHOOTER.scr:76
    -- traceon
    -- delete!!!
    ctx:getParam(0, "param0") -- ILSROTATESHOOTER.scr:83
    ctx:getParam(1, "param1") -- ILSROTATESHOOTER.scr:84
    ctx:getParam(2, "param2") -- ILSROTATESHOOTER.scr:85
    ctx:addTrigger("Stop", "OnStop") -- ILSROTATESHOOTER.scr:87
    ctx:addTrigger("Start", "Onstart") -- ILSROTATESHOOTER.scr:88
    do return ctx:exit("") end -- ILSROTATESHOOTER.scr:89
end

return script
