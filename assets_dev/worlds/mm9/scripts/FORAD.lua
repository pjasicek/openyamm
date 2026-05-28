-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FORAD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "BaseWander.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "BaseMelee.inc" }

-- forad.scr
-- By Timmy
-- handles forad's stuff
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- FORAD.scr:23
    if not ctx:hasKey(480) then -- FORAD.scr:26-27
        ctx:giveKey(480) -- FORAD.scr:28
        ctx:giveExp(800) -- FORAD.scr:29
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- FORAD.scr:30
    end -- FORAD.scr:31
    ctx:command("set", "bTalking, TRUE") -- FORAD.scr:33
    ctx:command("stop", "") -- FORAD.scr:34
    mm9.gosub(script, ctx, "BasewanderStop") -- FORAD.scr:35
    ctx:getParam(0, "g_hobject") -- FORAD.scr:36
    ctx:command("faceobject", "g_hobject 200 DoNothing") -- FORAD.scr:37
    -- DoRude 2
    ctx:command("playanim", "bow DoNothing") -- FORAD.scr:39
    -- Playsound voices\NPC\NPC_002.wav, Onexit, 100, 24000, FALSE, 100
    do return ctx:exit("") end -- FORAD.scr:41
end

script.labels["OnRude"] = function(ctx)
    -- FORAD.scr:46
    if ctx:hasKey(104) then -- FORAD.scr:50-51
        ctx:command("onfoundplayer", "") -- FORAD.scr:52
        mm9.gosub(script, ctx, "BaseInit") -- FORAD.scr:53
        ctx:command("set", "bHostile, TRUE") -- FORAD.scr:54
        do return ctx:exit("") end -- FORAD.scr:55
    end -- FORAD.scr:56
    mm9.gosub(script, ctx, "Forad") -- FORAD.scr:57
    do return ctx:exit("") end -- FORAD.scr:58
end

script.labels["Forad"] = function(ctx)
    -- FORAD.scr:61
    -- forad joins the party
    -- XP
    if not ctx:hasKey(368) then -- FORAD.scr:69-70
        ctx:giveExp(4000) -- FORAD.scr:71
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- FORAD.scr:72
        ctx:giveKey(368) -- FORAD.scr:73
    end -- FORAD.scr:74
    ctx:command("set", "bTalking, false") -- FORAD.scr:77
    if ctx:hasKey(29) then -- FORAD.scr:78-79
        -- Playsound voices\NPC\NPC_002.wav, Onexit, 100, 24000, FALSE, 100
        ctx:command("getmyhandle", "g_hmyobject") -- FORAD.scr:81
        ctx:command("removeobject", "g_hmyobject") -- FORAD.scr:82
        do return ctx:exit("") end -- FORAD.scr:83
    end -- FORAD.scr:84
    do return ctx:exit("") end -- FORAD.scr:86
end

script.labels["Onexit"] = function(ctx)
    -- FORAD.scr:88
    do return ctx:exit("") end -- FORAD.scr:91
end

script.labels["DeleteCheck"] = function(ctx)
    -- FORAD.scr:96
    if ctx:hasKey(29) then -- FORAD.scr:101-102
        ctx:command("getmyhandle", "g_hmyobject") -- FORAD.scr:103
        ctx:command("removeobject", "g_hmyobject") -- FORAD.scr:104
        do return ctx:exit("") end -- FORAD.scr:105
    end -- FORAD.scr:106
    do return ctx:exit("") end -- FORAD.scr:108
end

script.labels["Vanish"] = function(ctx)
    -- FORAD.scr:111
    ctx:command("getmyhandle", "g_hobject") -- FORAD.scr:114
    ctx:command("clearflag", "g_hobject, visible") -- FORAD.scr:115
    ctx:command("clearflag", "g_hobject, solid") -- FORAD.scr:116
    ctx:command("clearflag", "g_hobject, gravity") -- FORAD.scr:117
    do return ctx:exit("") end -- FORAD.scr:118
end

script.labels["OnAppear"] = function(ctx)
    -- FORAD.scr:121
    ctx:command("getmyhandle", "g_hobject") -- FORAD.scr:124
    ctx:command("setflag", "g_hobject, visible") -- FORAD.scr:125
    ctx:command("setflag", "g_hobject, solid") -- FORAD.scr:126
    ctx:command("setflag", "g_hobject, gravity") -- FORAD.scr:127
    ctx:command("onfoundplayer", "OnTarget 256") -- FORAD.scr:128
    do return ctx:exit("") end -- FORAD.scr:129
end

script.labels["OnTarget"] = function(ctx)
    -- FORAD.scr:132
    if ctx:condition("bTalking==TRUE") then -- FORAD.scr:135
        do return ctx:exit("") end -- FORAD.scr:136
    end -- FORAD.scr:137
    ctx:getParam(0, "g_hplayer") -- FORAD.scr:139
    ctx:command("target", "g_hplayer") -- FORAD.scr:140
    ctx:command("ontargetwithindist", "16 Talk") -- FORAD.scr:141
    do return ctx:exit("") end -- FORAD.scr:142
end

script.labels["OnDeath"] = function(ctx)
    -- FORAD.scr:145
    if ctx:hasKey(494) then -- FORAD.scr:149-150
        do return ctx:exit("") end -- FORAD.scr:151
    end -- FORAD.scr:152
    ctx:giveExp(194000) -- FORAD.scr:154
    ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- FORAD.scr:155
    mm9.gosub(script, ctx, "OnDeath") -- FORAD.scr:156
    ctx:giveKey(494) -- FORAD.scr:157
    do return ctx:exit("") end -- FORAD.scr:158
end

script.labels["Talk"] = function(ctx)
    -- FORAD.scr:161
    ctx:command("stop", "") -- FORAD.scr:164
    ctx:command("set", "bTalking, TRUE") -- FORAD.scr:165
    ctx:doRude(2) -- FORAD.scr:166
    do return ctx:exit("") end -- FORAD.scr:167
end

script.labels["Main"] = function(ctx)
    -- FORAD.scr:170
    -- TraceOn ;delete me!!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- FORAD.scr:175
    ctx:addTrigger("Use", "OnUse") -- FORAD.scr:176
    ctx:addTrigger("Appear", "OnAppear") -- FORAD.scr:177
    ctx:getParam(0, "sForad") -- FORAD.scr:178
    if ctx:condition("sForad!=HATE") then -- FORAD.scr:179
        mm9.gosub(script, ctx, "DeleteCheck") -- FORAD.scr:180
    else -- FORAD.scr:181
        mm9.gosub(script, ctx, "Vanish") -- FORAD.scr:182
    end -- FORAD.scr:183
    do return ctx:exit("") end -- FORAD.scr:185
end

return script
