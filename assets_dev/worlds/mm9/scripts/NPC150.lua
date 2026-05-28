-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC150.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC150.scr
-- timmy
-- handles Scandlan the Long tounge's speech
-- flag variables
script.labels["OnStart"] = function(ctx)
    -- NPC150.scr:20
    ctx:hasKey(5020, "bSpeak") -- NPC150.scr:23
    if ctx:condition("bSpeak==TRUE") then -- NPC150.scr:24
        do return ctx:exit("") end -- NPC150.scr:25
    end -- NPC150.scr:26
    ctx:setPropNumber("DoRude", "False") -- NPC150.scr:28
    ctx:command("getobjecthandle", "Broccan g_hobject") -- NPC150.scr:30
    ctx:command("target", "g_hobject") -- NPC150.scr:31
    ctx:trigger("g_hobject", "Target") -- NPC150.scr:32
    ctx:giveKey(5020) -- NPC150.scr:34
    ctx:command("loopanim", "conv2 0 DoNothing") -- NPC150.scr:35
    ctx:command("playsound", "voices\\cinema\\NewGame\\01.wav, DoNothing, 100, 768, FALSE, 100") -- NPC150.scr:36
    ctx:command("wait", "1 6.5, Trigger2") -- NPC150.scr:37
    do return ctx:exit("") end -- NPC150.scr:38
end

script.labels["Trigger2"] = function(ctx)
    -- NPC150.scr:42
    mm9.gosub(script, ctx, "Onstop") -- NPC150.scr:45
    ctx:command("getobjecthandle", "Broccan g_hobject") -- NPC150.scr:46
    ctx:trigger("g_hobject", "Speak2") -- NPC150.scr:47
    do return ctx:exit("") end -- NPC150.scr:48
end

script.labels["OnSpeak3"] = function(ctx)
    -- NPC150.scr:52
    ctx:command("loopanim", "conv2 0 DoNothing") -- NPC150.scr:55
    ctx:command("playsound", "voices\\cinema\\NewGame\\03.wav, DoNothing, 100, 768, FALSE, 100") -- NPC150.scr:56
    ctx:command("wait", "1 13.3, Trigger4") -- NPC150.scr:57
    do return ctx:exit("") end -- NPC150.scr:58
end

script.labels["Trigger4"] = function(ctx)
    -- NPC150.scr:62
    mm9.gosub(script, ctx, "Onstop") -- NPC150.scr:65
    ctx:command("getobjecthandle", "Broccan g_hobject") -- NPC150.scr:66
    ctx:trigger("g_hobject", "Speak4") -- NPC150.scr:67
    do return ctx:exit("") end -- NPC150.scr:68
end

script.labels["OnSpeak5"] = function(ctx)
    -- NPC150.scr:72
    ctx:command("loopanim", "conv5 0 DoNothing") -- NPC150.scr:75
    ctx:command("playsound", "voices\\cinema\\NewGame\\05.wav, DoNothing, 100, 768, FALSE, 100") -- NPC150.scr:76
    ctx:command("wait", "1 18.5, Trigger6") -- NPC150.scr:77
    do return ctx:exit("") end -- NPC150.scr:78
end

script.labels["Trigger6"] = function(ctx)
    -- NPC150.scr:82
    mm9.gosub(script, ctx, "Onstop") -- NPC150.scr:85
    ctx:command("getobjecthandle", "Broccan g_hobject") -- NPC150.scr:86
    ctx:trigger("g_hobject", "Speak6") -- NPC150.scr:87
    do return ctx:exit("") end -- NPC150.scr:88
end

script.labels["OnSpeak7"] = function(ctx)
    -- NPC150.scr:92
    ctx:command("loopanim", "conv4 0 DoNothing") -- NPC150.scr:95
    ctx:command("playsound", "voices\\cinema\\NewGame\\07.wav, DoNothing, 100, 768, FALSE, 100") -- NPC150.scr:96
    ctx:command("wait", "1 7, Trigger8") -- NPC150.scr:97
    do return ctx:exit("") end -- NPC150.scr:98
end

script.labels["Trigger8"] = function(ctx)
    -- NPC150.scr:102
    mm9.gosub(script, ctx, "Onstop") -- NPC150.scr:105
    ctx:command("getobjecthandle", "Broccan g_hobject") -- NPC150.scr:106
    ctx:trigger("g_hobject", "Speak8") -- NPC150.scr:107
    do return ctx:exit("") end -- NPC150.scr:108
end

script.labels["OnSpeak9"] = function(ctx)
    -- NPC150.scr:112
    ctx:command("loopanim", "conv5 0 DoNothing") -- NPC150.scr:115
    ctx:command("playsound", "voices\\cinema\\NewGame\\09.wav, DoNothing, 100, 768, FALSE, 100") -- NPC150.scr:116
    ctx:command("wait", "1 12.5, Trigger10") -- NPC150.scr:117
    do return ctx:exit("") end -- NPC150.scr:118
end

script.labels["Trigger10"] = function(ctx)
    -- NPC150.scr:122
    mm9.gosub(script, ctx, "Onstop") -- NPC150.scr:125
    ctx:command("getobjecthandle", "Broccan g_hobject") -- NPC150.scr:126
    ctx:trigger("g_hobject", "Speak10") -- NPC150.scr:127
    do return ctx:exit("") end -- NPC150.scr:128
end

script.labels["OnSpeak11"] = function(ctx)
    -- NPC150.scr:131
    ctx:command("loopanim", "conv5 0 DoNothing") -- NPC150.scr:134
    ctx:command("playsound", "voices\\cinema\\NewGame\\11.wav, DoNothing, 100, 768, FALSE, 100") -- NPC150.scr:135
    ctx:command("wait", "1 8.5, Trigger12") -- NPC150.scr:136
    do return ctx:exit("") end -- NPC150.scr:137
end

script.labels["Trigger12"] = function(ctx)
    -- NPC150.scr:141
    ctx:command("target", "Null") -- NPC150.scr:143
    mm9.gosub(script, ctx, "Onstop") -- NPC150.scr:144
    ctx:command("getobjecthandle", "Broccan g_hobject") -- NPC150.scr:145
    ctx:trigger("g_hobject", "Speak12") -- NPC150.scr:146
    ctx:command("wait", "1 1 OnSpeak12") -- NPC150.scr:147
    do return ctx:exit("") end -- NPC150.scr:148
end

script.labels["OnSpeak12"] = function(ctx)
    -- NPC150.scr:151
    ctx:command("loopanim", "conv5 0 DoNothing") -- NPC150.scr:154
    ctx:command("playsound", "voices\\cinema\\NewGame\\12.wav, DoNothing, 100, 768, FALSE, 100") -- NPC150.scr:155
    -- wait 1 18.5, Trigger12
    ctx:setPropNumber("DoRude", "TRUE") -- NPC150.scr:157
    do return ctx:exit("") end -- NPC150.scr:158
end

script.labels["OnLost"] = function(ctx)
    -- NPC150.scr:162
    do return ctx:exit("TRUE") end -- NPC150.scr:165
end

script.labels["Init"] = function(ctx)
    -- NPC150.scr:168
    ctx:command("onfoundplayer", "OnStart") -- NPC150.scr:171
    ctx:command("onlosttarget", "ONLost") -- NPC150.scr:172
    do return ctx:exit("TRUE") end -- NPC150.scr:173
end

script.labels["OnStop"] = function(ctx)
    -- NPC150.scr:176
    -- stop
    -- Loopanim stand 0 DoNothing
    do return ctx:exit("") end -- NPC150.scr:180
end

script.labels["Main"] = function(ctx)
    -- NPC150.scr:183
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Start", "OnStart") -- NPC150.scr:188
    ctx:addTrigger("Speak3", "OnSpeak3") -- NPC150.scr:189
    ctx:addTrigger("Speak5", "OnSpeak5") -- NPC150.scr:190
    ctx:addTrigger("Speak7", "OnSpeak7") -- NPC150.scr:191
    ctx:addTrigger("Speak9", "OnSpeak9") -- NPC150.scr:192
    ctx:addTrigger("Speak11", "OnSpeak11") -- NPC150.scr:193
    -- AddTrigger Speak12 OnSpeak12
    mm9.gosub(script, ctx, "Init") -- NPC150.scr:195
    do return ctx:exit("") end -- NPC150.scr:197
end

return script
