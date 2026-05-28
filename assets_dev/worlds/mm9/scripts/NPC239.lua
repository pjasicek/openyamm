-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC239.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "United.inc" }

-- NPC239.scr
-- timmy
-- handles Kira the Cold voice and quest stuff
-- edited by Bones 03/25/03
-- TELP Patch 1.3 -- delays Kira's return
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["Init"] = function(ctx)
    -- NPC239.scr:30
    -- loopanim Sit 0 DoNothing
    if ctx:hasKey(40) then -- NPC239.scr:36-37
        ctx:command("set", "bVanish TRUE") -- NPC239.scr:38
        mm9.gosub(script, ctx, "vanish") -- NPC239.scr:39
        ctx:command("getobjecthandle", "MarkeProp0 g_hobject") -- NPC239.scr:40
        ctx:command("removeobject", "g_hobject") -- NPC239.scr:41
    end -- NPC239.scr:42
    if ctx:hasKey(108) then -- NPC239.scr:44-45
        ctx:command("set", "bVanish False") -- NPC239.scr:46
        mm9.gosub(script, ctx, "Vanish") -- NPC239.scr:47
    end -- NPC239.scr:48
    do return ctx:exit("") end -- NPC239.scr:49
end

script.labels["Vanish"] = function(ctx)
    -- NPC239.scr:54
    ctx:command("getmyhandle", "g_hobject") -- NPC239.scr:57
    if ctx:condition("bVanish==TRUE") then -- NPC239.scr:59
        ctx:command("clearflag", "g_hobject, visible") -- NPC239.scr:60
        ctx:command("clearflag", "g_hobject, solid") -- NPC239.scr:61
        ctx:command("clearflag", "g_hobject, gravity") -- NPC239.scr:62
        do return ctx:exit("") end -- NPC239.scr:63
    else -- NPC239.scr:64
        ctx:command("setflag", "g_hobject, visible") -- NPC239.scr:65
        ctx:command("setflag", "g_hobject, solid") -- NPC239.scr:66
        ctx:command("setflag", "g_hobject, gravity") -- NPC239.scr:67
        do return ctx:exit("") end -- NPC239.scr:68
    end -- NPC239.scr:69
    do return ctx:exit("") end -- NPC239.scr:71
end

script.labels["OnRude"] = function(ctx)
    -- NPC239.scr:74
    mm9.gosub(script, ctx, "Loveletter") -- NPC239.scr:77
    mm9.gosub(script, ctx, "honkys") -- NPC239.scr:78
    mm9.gosub(script, ctx, "mountainpass") -- NPC239.scr:79
    mm9.gosub(script, ctx, "united") -- NPC239.scr:80
    mm9.gosub(script, ctx, "treaty") -- NPC239.scr:81
    do return ctx:exit("") end -- NPC239.scr:82
end

script.labels["treaty"] = function(ctx)
    -- NPC239.scr:86
    -- treaty Quest
    ctx:hasKey(181, "keycheck") -- NPC239.scr:93
    if ctx:condition("keycheck==0") then -- NPC239.scr:94
        ctx:hasKey(89, "keycheck") -- NPC239.scr:95
        if ctx:condition("keycheck==1") then -- NPC239.scr:96
            ctx:giveKey(181) -- NPC239.scr:97
            ctx:giveExp(12000) -- NPC239.scr:98
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC239.scr:99
            ctx:giveItem(401) -- NPC239.scr:100
            do return ctx:exit("") end -- NPC239.scr:101
        end -- NPC239.scr:102
    end -- NPC239.scr:103
    -- End treaty quest
    do return ctx:exit("") end -- NPC239.scr:107
end

script.labels["loveletter"] = function(ctx)
    -- NPC239.scr:110
    -- Love Letter Quest
    ctx:hasKey(147, "keycheck") -- NPC239.scr:117
    if ctx:condition("keycheck==0") then -- NPC239.scr:118
        ctx:hasKey(23, "keycheck") -- NPC239.scr:119
        if ctx:condition("keycheck==1") then -- NPC239.scr:120
            ctx:takeItem(247) -- NPC239.scr:121
            ctx:giveKey(147) -- NPC239.scr:122
            ctx:giveExp(12000) -- NPC239.scr:123
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC239.scr:124
            do return ctx:exit("") end -- NPC239.scr:125
        end -- NPC239.scr:126
    end -- NPC239.scr:127
    -- End Love Letter quest
    do return ctx:exit("") end -- NPC239.scr:132
end

script.labels["honkys"] = function(ctx)
    -- NPC239.scr:136
    -- Rid Thronheim of Honkies Quest
    ctx:hasKey(146, "keycheck") -- NPC239.scr:143
    if ctx:condition("keycheck==0") then -- NPC239.scr:144
        ctx:hasKey(78, "keycheck") -- NPC239.scr:145
        if ctx:condition("keycheck==1") then -- NPC239.scr:146
            ctx:giveExp(40000) -- NPC239.scr:147
            ctx:giveKey(146) -- NPC239.scr:148
            ctx:giveGold(7000) -- NPC239.scr:149
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC239.scr:150
            do return ctx:exit("") end -- NPC239.scr:151
        end -- NPC239.scr:152
    end -- NPC239.scr:153
    -- End Thronheim of Honkies Quest
    do return ctx:exit("") end -- NPC239.scr:157
end

script.labels["MountainPass"] = function(ctx)
    -- NPC239.scr:160
    -- Open Mountain Pass Quest
    ctx:hasKey(152, "keycheck") -- NPC239.scr:168
    if ctx:condition("keycheck==0") then -- NPC239.scr:169
        ctx:hasKey(81, "keycheck") -- NPC239.scr:170
        if ctx:condition("keycheck==1") then -- NPC239.scr:171
            ctx:giveExp(120000) -- NPC239.scr:172
            ctx:giveKey(152) -- NPC239.scr:173
            ctx:giveGold(12000) -- NPC239.scr:174
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- NPC239.scr:175
            do return ctx:exit("") end -- NPC239.scr:176
        end -- NPC239.scr:177
    end -- NPC239.scr:178
    -- End Open Moutain Pass Quest
    do return ctx:exit("") end -- NPC239.scr:184
end

script.labels["OnUse"] = function(ctx)
    -- NPC239.scr:188
    -- loopanim Sit 0 DoNothing
    ctx:command("playsound", "voices\\NPC\\NPC_239.wav, Onexit, 100, 240, FALSE, 100") -- NPC239.scr:192
    mm9.gosub(script, ctx, "OnCheck") -- NPC239.scr:193
    -- DoRude 239
    do return ctx:exit("") end -- NPC239.scr:195
end

script.labels["OnExit"] = function(ctx)
    -- NPC239.scr:198
    do return ctx:exit("") end -- NPC239.scr:201
end

script.labels["givekey"] = function(ctx)
    -- NPC239.scr:204
    if not ctx:hasKey(180) then -- NPC239.scr:206-207
        if ctx:hasKey(88) then -- NPC239.scr:208-209
            ctx:giveKey(180) -- NPC239.scr:210
            do return ctx:exit("") end -- NPC239.scr:211
        end -- NPC239.scr:212
    end -- NPC239.scr:213
    do return ctx:exit("") end -- NPC239.scr:215
end

script.labels["OnKillMarkel"] = function(ctx)
    -- NPC239.scr:218
    ctx:command("getobjecthandle", "Prop16 g_hobject") -- NPC239.scr:221
    ctx:trigger("g_hobject", "play") -- NPC239.scr:222
    ctx:command("getobjecthandle", "MarkeProp g_hobject") -- NPC239.scr:223
    ctx:command("removeobject", "g_hobject") -- NPC239.scr:224
    ctx:command("getobjecthandle", "MarkeProp0 g_hobject") -- NPC239.scr:225
    ctx:command("setflag", "g_hobject, visible") -- NPC239.scr:226
    do return ctx:exit("") end -- NPC239.scr:227
end

script.labels["Main"] = function(ctx)
    -- NPC239.scr:230
    -- traceon
    -- Don't Forget to Delete this!
    ctx:command("@m", "6 : 00 Givekey Givekey") -- NPC239.scr:236
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC239.scr:237
    ctx:addTrigger("Use", "OnUse") -- NPC239.scr:239
    ctx:addTrigger("KillMarkel", "OnKillMarkel") -- NPC239.scr:240
    ctx:command("set", "Jarl, Kira") -- NPC239.scr:241
    mm9.gosub(script, ctx, "UnitedInit") -- NPC239.scr:242
    ctx:command("onpoststartworld", "Init") -- NPC239.scr:243
    ctx:command("onpostminisaveload", "Init") -- NPC239.scr:244
    ctx:command("onpostsaveload", "Init") -- NPC239.scr:245
    ctx:command("wait", "1 .1 Init") -- NPC239.scr:246
    do return ctx:exit("") end -- NPC239.scr:247
end

return script
