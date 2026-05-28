-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EVERSTRIKE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- givetake.scr
-- 10/4
-- timmy
-- gives party specific item
-- flag variables
-- Parameters
-- P0 Item number of item to give
script.labels["OnUse"] = function(ctx)
    -- EVERSTRIKE.scr:31
    if ctx:hasKey(238) then -- EVERSTRIKE.scr:33-34
        ctx:giveKey(241) -- EVERSTRIKE.scr:35
        ctx:giveItem(184) -- EVERSTRIKE.scr:36
        ctx:command("getmyhandle", "g_hmyobject") -- EVERSTRIKE.scr:37
        ctx:command("removeobject", "g_hmyobject") -- EVERSTRIKE.scr:38
        do return ctx:exit("") end -- EVERSTRIKE.scr:39
    end -- EVERSTRIKE.scr:40
    do return ctx:exit("") end -- EVERSTRIKE.scr:41
end

script.labels["Remove"] = function(ctx)
    -- EVERSTRIKE.scr:44
    ctx:command("getmyhandle", "g_hobject") -- EVERSTRIKE.scr:47
    ctx:command("clearflag", "g_hobject, visible") -- EVERSTRIKE.scr:48
    ctx:command("clearflag", "g_hobject, solid") -- EVERSTRIKE.scr:49
    ctx:command("clearflag", "g_hobject, gravity") -- EVERSTRIKE.scr:50
    do return ctx:exit("") end -- EVERSTRIKE.scr:51
end

script.labels["Appear"] = function(ctx)
    -- EVERSTRIKE.scr:53
    ctx:command("getmyhandle", "g_hobject") -- EVERSTRIKE.scr:57
    ctx:command("setflag", "g_hobject, visible") -- EVERSTRIKE.scr:58
    ctx:command("setflag", "g_hobject, solid") -- EVERSTRIKE.scr:59
    ctx:command("setflag", "g_hobject, gravity") -- EVERSTRIKE.scr:60
    do return ctx:exit("") end -- EVERSTRIKE.scr:61
end

script.labels["Init"] = function(ctx)
    -- EVERSTRIKE.scr:65
    if ctx:hasKey(241) then -- EVERSTRIKE.scr:68-69
        mm9.gosub(script, ctx, "Remove") -- EVERSTRIKE.scr:70
    end -- EVERSTRIKE.scr:71
    if ctx:hasKey(238) then -- EVERSTRIKE.scr:73-74
        mm9.gosub(script, ctx, "appear") -- EVERSTRIKE.scr:75
    else -- EVERSTRIKE.scr:76
        mm9.gosub(script, ctx, "remove") -- EVERSTRIKE.scr:77
    end -- EVERSTRIKE.scr:78
    do return ctx:exit("") end -- EVERSTRIKE.scr:79
end

script.labels["Main"] = function(ctx)
    -- EVERSTRIKE.scr:82
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- EVERSTRIKE.scr:87
    ctx:command("wait", "1 1 Init") -- EVERSTRIKE.scr:88
    do return ctx:exit("") end -- EVERSTRIKE.scr:90
end

return script
