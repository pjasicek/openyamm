-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC90.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 13, path = "basedoor.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "followplayer.inc" }

-- NPC90.scr
-- timmy
-- handles Ivsar Forktooth voice and stuff
-- edited by Bones 05/25/03
-- TELP Patch 1.3 -- allows Isvar to be removed from prison
-- moves him into site after leaving prison
-- prevents premature exit from prison exit dialog
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["BD_DoorOpen"] = function(ctx)
    -- NPC90.scr:36
    ctx:command("g_bdooropening", "= FALSE") -- NPC90.scr:38
    ctx:command("resumewait", "-1") -- NPC90.scr:40
    ctx:command("gettarget", "g_hObject") -- NPC90.scr:42
    if ctx:condition("g_hObject==NULL") then -- NPC90.scr:44
        if ctx:condition("g_bWasRunning==TRUE") then -- NPC90.scr:45
            ctx:command("run", "") -- NPC90.scr:46
        else -- NPC90.scr:47
            ctx:command("walk", "") -- NPC90.scr:48
        end -- NPC90.scr:49
    else -- NPC90.scr:50
        if ctx:condition("g_bWasRunning==TRUE") then -- NPC90.scr:51
            ctx:command("runto", "g_hObject") -- NPC90.scr:52
        else -- NPC90.scr:53
            ctx:command("walkto", "g_hObject") -- NPC90.scr:54
        end -- NPC90.scr:55
    end -- NPC90.scr:56
    ctx:command("restorepath", "") -- NPC90.scr:58
    mm9.gosub(script, ctx, "Followstart") -- NPC90.scr:59
    do return ctx:exit("") end -- NPC90.scr:61
end

script.labels["OnUse"] = function(ctx)
    -- NPC90.scr:64
    ctx:command("onfoundplayer", "") -- NPC90.scr:67
    if ctx:condition("params==drangheim") then -- NPC90.scr:69
        ctx:giveKey(194) -- NPC90.scr:70
        ctx:command("getmyhandle", "g_hMyObject") -- NPC90.scr:72
        if ctx:condition("sWhoAmI==Well") then -- NPC90.scr:74
            ctx:command("getobjecthandle", "PrisonerHuman2MaleA0 g_hobject") -- NPC90.scr:75
            ctx:command("removeobject", "g_hobject") -- NPC90.scr:76
            ctx:command("setpos", "g_hMyObject -2525 948 397") -- NPC90.scr:78
        else -- NPC90.scr:80
            ctx:command("getobjecthandle", "PrisonerHuman2MaleA1 g_hobject") -- NPC90.scr:81
            ctx:command("removeobject", "g_hobject") -- NPC90.scr:82
            ctx:command("setpos", "g_hMyObject -4253 817 -6191") -- NPC90.scr:84
        end -- NPC90.scr:86
        ctx:command("getplayerhandle", "g_hPlayer") -- NPC90.scr:88
        ctx:command("faceobject", "g_hPlayer") -- NPC90.scr:89
        ctx:command("target", "g_hPlayer TRUE") -- NPC90.scr:90
        ctx:command("playsound", "voices\\NPC\\NPC_090.wav, DoNothing, 100, 240, FALSE, 100") -- NPC90.scr:92
        ctx:doRude(90) -- NPC90.scr:93
        do return ctx:exit("") end -- NPC90.scr:94
    end -- NPC90.scr:96
    ctx:command("playsound", "voices\\NPC\\NPC_090.wav, DoNothing, 100, 240, FALSE, 100") -- NPC90.scr:98
    do return ctx:exit("") end -- NPC90.scr:101
end

script.labels["Onrude"] = function(ctx)
    -- NPC90.scr:104
    if ctx:hasKey(194) then -- NPC90.scr:108-109
        if not ctx:hasKey(242) then -- NPC90.scr:110-111
            ctx:doRude(90) -- NPC90.scr:112
            do return ctx:exit("") end -- NPC90.scr:113
        end -- NPC90.scr:114
    end -- NPC90.scr:115
    ctx:takeKey(194) -- NPC90.scr:117
    mm9.gosub(script, ctx, "FollowPlayer") -- NPC90.scr:119
    do return ctx:exit("") end -- NPC90.scr:121
end

script.labels["FollowPlayer"] = function(ctx)
    -- NPC90.scr:127
    if ctx:condition("params==DRANGHEIM") then -- NPC90.scr:130
        do return ctx:exit("") end -- NPC90.scr:131
    end -- NPC90.scr:132
    if ctx:hasKey(21) then -- NPC90.scr:134-135
        do return ctx:exit("") end -- NPC90.scr:136
    end -- NPC90.scr:137
    if ctx:condition("params==sturmgaard") then -- NPC90.scr:139
        ctx:giveKey(196) -- NPC90.scr:140
    end -- NPC90.scr:141
    ctx:giveKey(5006) -- NPC90.scr:142
    mm9.gosub(script, ctx, "followstart") -- NPC90.scr:143
    do return ctx:exit("") end -- NPC90.scr:146
end

script.labels["Init"] = function(ctx)
    -- NPC90.scr:151
    ctx:command("getmyhandle", "g_hobject") -- NPC90.scr:154
    mm9.gosub(script, ctx, "basedoorinit") -- NPC90.scr:155
    -- ***********DRANGHEIM**********
    if ctx:condition("params==drangheim") then -- NPC90.scr:159
        ctx:command("getmyhandle", "g_hobject") -- NPC90.scr:160
        if not ctx:hasKey(17) then -- NPC90.scr:161-162
            ctx:command("clearflag", "g_hobject, visible") -- NPC90.scr:164
            ctx:command("clearflag", "g_hobject, solid") -- NPC90.scr:165
            ctx:command("clearflag", "g_hobject, gravity") -- NPC90.scr:166
            do return ctx:exit("") end -- NPC90.scr:167
        else -- NPC90.scr:168
            ctx:command("setflag", "g_hobject, visible") -- NPC90.scr:169
            ctx:command("setflag", "g_hobject, solid") -- NPC90.scr:170
            ctx:command("setflag", "g_hobject, gravity") -- NPC90.scr:171
            ctx:command("onfoundplayer", "OnUse") -- NPC90.scr:172
        end -- NPC90.scr:173
        if ctx:hasKey(194) then -- NPC90.scr:175-176
            ctx:command("getmyhandle", "g_hmyobject") -- NPC90.scr:177
            ctx:command("removeobject", "g_hmyobject") -- NPC90.scr:178
            do return ctx:exit("") end -- NPC90.scr:179
        end -- NPC90.scr:180
        if ctx:hasKey(242) then -- NPC90.scr:182-183
            ctx:command("getmyhandle", "g_hobject") -- NPC90.scr:184
            ctx:command("clearflag", "g_hobject, visible") -- NPC90.scr:185
            ctx:command("clearflag", "g_hobject, solid") -- NPC90.scr:186
            ctx:command("clearflag", "g_hobject, gravity") -- NPC90.scr:187
            do return ctx:exit("") end -- NPC90.scr:188
        else -- NPC90.scr:189
            ctx:command("setflag", "g_hobject, visible") -- NPC90.scr:190
            ctx:command("setflag", "g_hobject, solid") -- NPC90.scr:191
            ctx:command("setflag", "g_hobject, gravity") -- NPC90.scr:192
            ctx:command("onfoundplayer", "OnUse") -- NPC90.scr:193
            do return ctx:exit("") end -- NPC90.scr:194
        end -- NPC90.scr:195
    end -- NPC90.scr:196
    -- ***********STURMFORD**********
    if ctx:condition("params==sturmgaard") then -- NPC90.scr:205
        ctx:command("getmyhandle", "g_hobject") -- NPC90.scr:206
        if not ctx:hasKey(242) then -- NPC90.scr:208-209
            ctx:command("clearflag", "g_hobject, visible") -- NPC90.scr:211
            ctx:command("clearflag", "g_hobject, solid") -- NPC90.scr:212
            ctx:command("clearflag", "g_hobject, gravity") -- NPC90.scr:213
            do return ctx:exit("") end -- NPC90.scr:214
        else -- NPC90.scr:215
            ctx:command("setflag", "g_hobject, visible") -- NPC90.scr:216
            ctx:command("setflag", "g_hobject, solid") -- NPC90.scr:217
            ctx:command("setflag", "g_hobject, gravity") -- NPC90.scr:218
            do return ctx:exit("") end -- NPC90.scr:219
        end -- NPC90.scr:220
        if ctx:hasKey(21) then -- NPC90.scr:222-223
            ctx:command("getobjecthandle", "IvsarMarker g_hobject") -- NPC90.scr:224
            ctx:command("getpos", "g_hobject xPos Ypos Zpos") -- NPC90.scr:225
            ctx:command("getmyhandle", "g_hmyobject") -- NPC90.scr:226
            ctx:command("setpos", "g_hmyobject xPos yPos zPos") -- NPC90.scr:227
            do return ctx:exit("") end -- NPC90.scr:228
        end -- NPC90.scr:229
    end -- NPC90.scr:231
    if ctx:condition("params==g_sPad5") then -- NPC90.scr:235
        if ctx:hasKey(242) then -- NPC90.scr:236-237
            ctx:command("getmyhandle", "g_hobject") -- NPC90.scr:238
            ctx:command("removeobject", "g_hobject") -- NPC90.scr:239
            do return ctx:exit("") end -- NPC90.scr:240
            -- deletes form prison if he's been rescued
        end -- NPC90.scr:243
    end -- NPC90.scr:244
    do return ctx:exit("") end -- NPC90.scr:246
end

script.labels["OnSTop"] = function(ctx)
    -- NPC90.scr:249
    mm9.gosub(script, ctx, "FollowStop") -- NPC90.scr:252
    ctx:command("getobjecthandle", "IvsarMarker g_hobject") -- NPC90.scr:253
    ctx:command("walkto", "g_hobject 32 OnArrive") -- NPC90.scr:254
    do return ctx:exit("") end -- NPC90.scr:255
end

script.labels["OnArrive"] = function(ctx)
    -- NPC90.scr:258
    ctx:command("stop", "") -- NPC90.scr:261
    do return ctx:exit("") end -- NPC90.scr:262
end

script.labels["Main"] = function(ctx)
    -- NPC90.scr:265
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "params") -- NPC90.scr:271
    ctx:getParam(1, "sWhoAmI") -- NPC90.scr:272
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC90.scr:273
    ctx:addTrigger("Use", "OnUse") -- NPC90.scr:274
    ctx:addTrigger("Stop", "OnSTop") -- NPC90.scr:275
    ctx:command("onpoststartworld", "Init") -- NPC90.scr:276
    ctx:command("onpostminisaveload", "Init") -- NPC90.scr:277
    ctx:command("onpostsaveload", "Init") -- NPC90.scr:278
    ctx:command("wait", "1 1 init") -- NPC90.scr:279
    do return ctx:exit("") end -- NPC90.scr:280
end

return script
