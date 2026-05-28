-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TAUNTMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- TauntMan.scr
-- timmy
-- Manager for Taunt script
-- edited by Bones 5/26/03
-- TELP Patch 1.3 -- Prevents lockup if in TB mode.
script.labels["OnStart"] = function(ctx)
    -- TAUNTMAN.scr:14
    if not ctx:hasKey(108) then -- TAUNTMAN.scr:17-18
        do return ctx:exit("") end -- TAUNTMAN.scr:19
    else -- TAUNTMAN.scr:20
        if ctx:hasKey(497) then -- TAUNTMAN.scr:21-22
            do return ctx:exit("") end -- TAUNTMAN.scr:23
        end -- TAUNTMAN.scr:24
    end -- TAUNTMAN.scr:25
    ctx:giveKey(497) -- TAUNTMAN.scr:27
    ctx:command("screenfadeout", "1") -- TAUNTMAN.scr:28
    ctx:command("wait", "1 1 FadeIn") -- TAUNTMAN.scr:29
    do return ctx:exit("") end -- TAUNTMAN.scr:30
end

script.labels["FadeIn"] = function(ctx)
    -- TAUNTMAN.scr:33
    ctx:command("letterbox", "True") -- TAUNTMAN.scr:36
    ctx:command("getobjecthandle", "TauntCam g_hobject") -- TAUNTMAN.scr:37
    ctx:trigger("g_hobject", "on") -- TAUNTMAN.scr:38
    ctx:command("screenfadein", "1") -- TAUNTMAN.scr:39
    ctx:command("getobjecthandle", "Door0 g_hobject") -- TAUNTMAN.scr:40
    ctx:trigger("g_hobject", "open") -- TAUNTMAN.scr:41
    ctx:command("wait", "1 1 TriggerNjam") -- TAUNTMAN.scr:42
    do return ctx:exit("") end -- TAUNTMAN.scr:43
end

script.labels["TriggerNjam"] = function(ctx)
    -- TAUNTMAN.scr:46
    -- Time to walk out of the Room
    ctx:command("getobjecthandle", "NjamtheMeddler0 g_hobject") -- TAUNTMAN.scr:51
    ctx:trigger("g_hobject", "start") -- TAUNTMAN.scr:52
    do return ctx:exit("") end -- TAUNTMAN.scr:53
end

script.labels["OnCloseUp"] = function(ctx)
    -- TAUNTMAN.scr:57
    -- switches to the Closeup Cam
    ctx:command("getobjecthandle", "Door0 g_hobject") -- TAUNTMAN.scr:62
    ctx:trigger("g_hobject", "Close") -- TAUNTMAN.scr:63
    ctx:command("getobjecthandle", "TauntCam g_hobject") -- TAUNTMAN.scr:64
    ctx:trigger("g_hobject", "off") -- TAUNTMAN.scr:65
    ctx:command("getobjecthandle", "TauntCamB g_hobject") -- TAUNTMAN.scr:66
    ctx:trigger("g_hobject", "on") -- TAUNTMAN.scr:67
    do return ctx:exit("") end -- TAUNTMAN.scr:68
end

script.labels["OnFarCam"] = function(ctx)
    -- TAUNTMAN.scr:74
    -- switches to the Closeup Cam
    ctx:command("getobjecthandle", "TauntCamB g_hobject") -- TAUNTMAN.scr:80
    ctx:trigger("g_hobject", "off") -- TAUNTMAN.scr:81
    ctx:command("getobjecthandle", "TauntCam g_hobject") -- TAUNTMAN.scr:82
    ctx:trigger("g_hobject", "on") -- TAUNTMAN.scr:83
    do return ctx:exit("") end -- TAUNTMAN.scr:84
end

script.labels["OnFadeOut"] = function(ctx)
    -- TAUNTMAN.scr:87
    ctx:command("screenfadeout", "1") -- TAUNTMAN.scr:90
    ctx:command("wait", "1 1 FadeOut2") -- TAUNTMAN.scr:91
    do return ctx:exit("") end -- TAUNTMAN.scr:92
end

script.labels["FadeOut2"] = function(ctx)
    -- TAUNTMAN.scr:96
    ctx:command("letterbox", "False") -- TAUNTMAN.scr:99
    ctx:command("getobjecthandle", "TauntCam g_hobject") -- TAUNTMAN.scr:100
    ctx:trigger("g_hobject", "off") -- TAUNTMAN.scr:101
    ctx:command("screenfadein", "1") -- TAUNTMAN.scr:102
    do return ctx:exit("") end -- TAUNTMAN.scr:103
end

script.labels["Main"] = function(ctx)
    -- TAUNTMAN.scr:106
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- TAUNTMAN.scr:112
    ctx:addTrigger("Arrive", "OnCloseUp") -- TAUNTMAN.scr:113
    ctx:addTrigger("VanishStart", "OnFarCam") -- TAUNTMAN.scr:114
    ctx:addTrigger("VanishDone", "OnFadeOut") -- TAUNTMAN.scr:115
    do return ctx:exit("") end -- TAUNTMAN.scr:117
end

script.labels["OnStart"] = function(ctx)
    -- TAUNTMAN.scr:120
    -- overloaded -- Bones
    if not ctx:hasKey(108) then -- TAUNTMAN.scr:124-125
        do return ctx:exit("") end -- TAUNTMAN.scr:126
    else -- TAUNTMAN.scr:127
        if ctx:hasKey(497) then -- TAUNTMAN.scr:128-129
            do return ctx:exit("") end -- TAUNTMAN.scr:130
        end -- TAUNTMAN.scr:131
    end -- TAUNTMAN.scr:132
    ctx:command("isturnbased", "g_nTemp") -- TAUNTMAN.scr:134
    if ctx:condition("g_nTemp == TRUE") then -- TAUNTMAN.scr:135
        ctx:command("screenfadeout", "1") -- TAUNTMAN.scr:136
        ctx:command("rollovertext", "18 0") -- TAUNTMAN.scr:137
        ctx:command("wait", "0 1 OnStart") -- TAUNTMAN.scr:138
        do return ctx:exit("") end -- TAUNTMAN.scr:139
    end -- TAUNTMAN.scr:140
    do return mm9.gotoLabel(script, ctx, "OnStart") end -- TAUNTMAN.scr:142
end

return script
