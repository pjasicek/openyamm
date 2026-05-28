-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GREATBOOKKEY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- GreatBookKey.scr
-- Handles the Great Book Key stuff
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- GREATBOOKKEY.scr:16
    if ctx:hasItem(243) then -- GREATBOOKKEY.scr:19-20
        ctx:giveItem(560) -- GREATBOOKKEY.scr:22
        ctx:giveItem(244) -- GREATBOOKKEY.scr:23
        ctx:giveItem(347) -- GREATBOOKKEY.scr:24
        ctx:command("getmyhandle", "g_hmyobject") -- GREATBOOKKEY.scr:25
        ctx:command("removeobject", "g_hmyobject") -- GREATBOOKKEY.scr:26
        ctx:giveKey(374) -- GREATBOOKKEY.scr:27
        do return ctx:exit("") end -- GREATBOOKKEY.scr:28
    else -- GREATBOOKKEY.scr:29
        ctx:giveItem(244) -- GREATBOOKKEY.scr:30
        do return ctx:exit("") end -- GREATBOOKKEY.scr:31
    end -- GREATBOOKKEY.scr:32
end

script.labels["OnAppear"] = function(ctx)
    -- GREATBOOKKEY.scr:34
    ctx:giveKey(375) -- GREATBOOKKEY.scr:37
    ctx:command("setflag", "g_hmyobject, visible") -- GREATBOOKKEY.scr:38
    ctx:command("setflag", "g_hmyobject, solid") -- GREATBOOKKEY.scr:39
    ctx:command("setflag", "g_hmyobject, gravity") -- GREATBOOKKEY.scr:40
    do return ctx:exit("") end -- GREATBOOKKEY.scr:41
end

script.labels["Init"] = function(ctx)
    -- GREATBOOKKEY.scr:43
    ctx:command("getmyhandle", "g_hmyobject") -- GREATBOOKKEY.scr:46
    if ctx:hasKey(374) then -- GREATBOOKKEY.scr:48-49
        ctx:command("getmyhandle", "g_hmyobject") -- GREATBOOKKEY.scr:50
        ctx:command("removeobject", "g_hmyobject") -- GREATBOOKKEY.scr:51
        do return ctx:exit("") end -- GREATBOOKKEY.scr:52
    end -- GREATBOOKKEY.scr:53
    if ctx:hasKey(375) then -- GREATBOOKKEY.scr:55-56
        ctx:command("setflag", "g_hmyobject, visible") -- GREATBOOKKEY.scr:57
        ctx:command("setflag", "g_hmyobject, solid") -- GREATBOOKKEY.scr:58
        ctx:command("setflag", "g_hmyobject, gravity") -- GREATBOOKKEY.scr:59
        do return ctx:exit("") end -- GREATBOOKKEY.scr:60
    else -- GREATBOOKKEY.scr:61
        ctx:command("clearflag", "g_hmyobject, visible") -- GREATBOOKKEY.scr:62
        ctx:command("clearflag", "g_hmyobject, solid") -- GREATBOOKKEY.scr:63
        ctx:command("clearflag", "g_hmyobject, gravity") -- GREATBOOKKEY.scr:64
        do return ctx:exit("") end -- GREATBOOKKEY.scr:65
    end -- GREATBOOKKEY.scr:66
    do return ctx:exit("") end -- GREATBOOKKEY.scr:67
end

script.labels["Main"] = function(ctx)
    -- GREATBOOKKEY.scr:70
    -- traceon
    ctx:addTrigger("Use", "OnUse") -- GREATBOOKKEY.scr:74
    ctx:addTrigger("appear", "OnAppear") -- GREATBOOKKEY.scr:75
    mm9.gosub(script, ctx, "Init") -- GREATBOOKKEY.scr:76
    do return ctx:exit("") end -- GREATBOOKKEY.scr:77
end

return script
