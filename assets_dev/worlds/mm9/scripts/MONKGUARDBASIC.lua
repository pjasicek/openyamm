-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MONKGUARDBASIC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "MonkHostility.inc" }
script.includes[#script.includes + 1] = { line = 14, path = "MonkSounds.inc" }

-- MonkGuardBasic.scr
-- by SJR
-- Purpose:standard monk, but with
-- checking for acts of
-- aggression
-- Params:
-- p0 = type (-1,0,1,2,3,4)->(chat,pray,hoe,broom,hammer,wash)
-- p1 = rude id
-- p3 = name of pray or work place
script.labels["Main"] = function(ctx)
    -- MONKGUARDBASIC.scr:35
    ctx:getParam(0, "MONK_TYPE") -- MONKGUARDBASIC.scr:37
    ctx:getParam(1, "MONK_RUDE") -- MONKGUARDBASIC.scr:38
    if ctx:condition("MONK_TYPE>=0") then -- MONKGUARDBASIC.scr:39
        ctx:getParam(2, "MONK_PLACE") -- MONKGUARDBASIC.scr:40
    end -- MONKGUARDBASIC.scr:41
    ctx:command("onpoststartworld", "InitMonkGuardBasic") -- MONKGUARDBASIC.scr:43
    ctx:command("onpostminisaveload", "InitMonkGuardBasic") -- MONKGUARDBASIC.scr:44
    ctx:addTrigger("use", "OnRudeEnter") -- MONKGUARDBASIC.scr:46
    ctx:onRudeExit("OnRudeExit", script.labels["OnRudeExit"]) -- MONKGUARDBASIC.scr:47
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:49
end

script.labels["InitMonkGuardBasic"] = function(ctx)
    -- MONKGUARDBASIC.scr:52
    mm9.gosub(script, ctx, "MS_Init") -- MONKGUARDBASIC.scr:54
    if ctx:condition("MONK_TYPE<0") then -- MONKGUARDBASIC.scr:56
    else -- MONKGUARDBASIC.scr:57
        ctx:command("getmyhandle", "hMe") -- MONKGUARDBASIC.scr:58
        ctx:command("getpos", "hMe, xMe,yMe,zMe") -- MONKGUARDBASIC.scr:59
        ctx:command("getobjecthandle", "MONK_PLACE, hPlace") -- MONKGUARDBASIC.scr:60
        -- only wander if not hammer or cloth
        if ctx:condition("MONK_TYPE==0") then -- MONKGUARDBASIC.scr:62
            ctx:addTrigger("gotopray", "StartPrayer") -- MONKGUARDBASIC.scr:63
        end -- MONKGUARDBASIC.scr:64
        if ctx:condition("MONK_TYPE<3") then -- MONKGUARDBASIC.scr:65
            mm9.gosub(script, ctx, "BaseWanderInit") -- MONKGUARDBASIC.scr:66
            mm9.gosub(script, ctx, "BaseWanderStartup") -- MONKGUARDBASIC.scr:67
        end -- MONKGUARDBASIC.scr:68
        -- only attach if not pray or chat
        if ctx:condition("MONK_TYPE>0") then -- MONKGUARDBASIC.scr:70
            mm9.gosub(script, ctx, "AttachTool") -- MONKGUARDBASIC.scr:71
            if ctx:condition("MONK_TYPE>2") then -- MONKGUARDBASIC.scr:72
                ctx:command("faceobject", "hPlace, 360, StartWork") -- MONKGUARDBASIC.scr:73
            end -- MONKGUARDBASIC.scr:74
        end -- MONKGUARDBASIC.scr:75
    end -- MONKGUARDBASIC.scr:76
    mm9.gosub(script, ctx, "InitMonkHostility") -- MONKGUARDBASIC.scr:78
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:80
end

script.labels["StartPrayer"] = function(ctx)
    -- MONKGUARDBASIC.scr:83
    if ctx:condition("hPlace!=0") then -- MONKGUARDBASIC.scr:85
        ctx:command("walkto", "hPlace, 100, Pray") -- MONKGUARDBASIC.scr:86
    end -- MONKGUARDBASIC.scr:87
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:89
end

script.labels["Pray"] = function(ctx)
    -- MONKGUARDBASIC.scr:92
    ctx:command("loopanim", "sPrayName, 0") -- MONKGUARDBASIC.scr:94
    ctx:command("wait", "0, 30, StopPrayer") -- MONKGUARDBASIC.scr:96
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:98
end

script.labels["StopPrayer"] = function(ctx)
    -- MONKGUARDBASIC.scr:101
    ctx:command("walktopos", "xMe,yMe,zMe, 10, DoNothing") -- MONKGUARDBASIC.scr:103
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:105
end

script.labels["StartWork"] = function(ctx)
    -- MONKGUARDBASIC.scr:108
    ctx:command("loopanim", "sAnimName, 0") -- MONKGUARDBASIC.scr:110
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:112
end

script.labels["StopWork"] = function(ctx)
    -- MONKGUARDBASIC.scr:115
    ctx:command("loopanim", "sPauseName, 0") -- MONKGUARDBASIC.scr:117
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:119
end

script.labels["AttachTool"] = function(ctx)
    -- MONKGUARDBASIC.scr:122
    if ctx:condition("MONK_TYPE==1") then -- MONKGUARDBASIC.scr:124
        ctx:command("attachprop", "\"MonkHoe.ABC\", \"MonkHoe.DTX\", \"Hoe\", hProp") -- MONKGUARDBASIC.scr:125
        ctx:command("sanimname", "= \"hoe\"") -- MONKGUARDBASIC.scr:126
        ctx:command("spausename", "= \"hoewait\"") -- MONKGUARDBASIC.scr:127
        ctx:command("fidget_name", "= \"HoeFidget\"") -- MONKGUARDBASIC.scr:128
    else -- MONKGUARDBASIC.scr:129
        if ctx:condition("MONK_TYPE==2") then -- MONKGUARDBASIC.scr:130
            ctx:command("attachprop", "\"MonkBroom.ABC\", \"MonkBroom.DTX\", \"Broom\", hProp") -- MONKGUARDBASIC.scr:131
            ctx:command("sanimname", "= \"sweep\"") -- MONKGUARDBASIC.scr:132
            ctx:command("spausename", "= \"sweepwait\"") -- MONKGUARDBASIC.scr:133
            ctx:command("fidget_name", "= \"SweepFidget\"") -- MONKGUARDBASIC.scr:134
        else -- MONKGUARDBASIC.scr:135
            if ctx:condition("MONK_TYPE==3") then -- MONKGUARDBASIC.scr:136
                ctx:command("attachprop", "\"MonkHammer.ABC\", \"MonkHammer.DTX\", \"Hammer\", hProp") -- MONKGUARDBASIC.scr:137
                ctx:command("sanimname", "= \"hammer\"") -- MONKGUARDBASIC.scr:138
                ctx:command("spausename", "= \"hammerwait\"") -- MONKGUARDBASIC.scr:139
                ctx:command("fidget_name", "= \"HammerFidget\"") -- MONKGUARDBASIC.scr:140
            else -- MONKGUARDBASIC.scr:141
                if ctx:condition("MONK_TYPE==4") then -- MONKGUARDBASIC.scr:142
                    ctx:command("attachprop", "\"MonkCloth.ABC\", \"MonkCloth.DTX\", \"Cloth\", hProp") -- MONKGUARDBASIC.scr:143
                    ctx:command("sanimname", "= \"wash\"") -- MONKGUARDBASIC.scr:144
                    ctx:command("spausename", "= \"washwait\"") -- MONKGUARDBASIC.scr:145
                    ctx:command("fidget_name", "= \"WashFidget\"") -- MONKGUARDBASIC.scr:146
                end -- MONKGUARDBASIC.scr:147
            end -- MONKGUARDBASIC.scr:148
        end -- MONKGUARDBASIC.scr:149
    end -- MONKGUARDBASIC.scr:150
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:152
end

script.labels["OnRudeEnter"] = function(ctx)
    -- MONKGUARDBASIC.scr:155
    ctx:getParam(0, "hSpeaker") -- MONKGUARDBASIC.scr:157
    if ctx:condition("MONK_TYPE<0") then -- MONKGUARDBASIC.scr:159
        ctx:command("faceobject", "hSpeaker, 360, DoNothing") -- MONKGUARDBASIC.scr:160
    else -- MONKGUARDBASIC.scr:161
        if ctx:condition("MONK_TYPE==0") then -- MONKGUARDBASIC.scr:162
            ctx:command("faceobject", "hSpeaker, 360, BaseWanderStop") -- MONKGUARDBASIC.scr:163
        else -- MONKGUARDBASIC.scr:164
            -- TL    loopAnim stand, 0
            ctx:command("playanim", "Fidget_Name, FidgetStand") -- MONKGUARDBASIC.scr:166
            -- TL
            ctx:command("faceobject", "hSpeaker, 360, DoNothing") -- MONKGUARDBASIC.scr:168
        end -- MONKGUARDBASIC.scr:169
    end -- MONKGUARDBASIC.scr:170
    ctx:command("pausewait", "-1") -- MONKGUARDBASIC.scr:172
    ctx:doRude("MONK_RUDE") -- MONKGUARDBASIC.scr:174
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:176
end

script.labels["FidgetStand"] = function(ctx)
    -- MONKGUARDBASIC.scr:180
    ctx:command("loopanim", "sPauseName 0 Donothing") -- MONKGUARDBASIC.scr:184
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:186
end

script.labels["OnRudeExit"] = function(ctx)
    -- MONKGUARDBASIC.scr:190
    ctx:command("resumewait", "-1") -- MONKGUARDBASIC.scr:193
    if ctx:condition("MONK_TYPE<0") then -- MONKGUARDBASIC.scr:195
    else -- MONKGUARDBASIC.scr:196
        if ctx:condition("MONK_TYPE<3") then -- MONKGUARDBASIC.scr:197
            mm9.gosub(script, ctx, "BaseWanderStart") -- MONKGUARDBASIC.scr:198
        else -- MONKGUARDBASIC.scr:199
            if ctx:condition("hPlace!=0") then -- MONKGUARDBASIC.scr:200
                ctx:command("faceobject", "hPlace, 360, StartWork") -- MONKGUARDBASIC.scr:201
            end -- MONKGUARDBASIC.scr:202
        end -- MONKGUARDBASIC.scr:203
    end -- MONKGUARDBASIC.scr:204
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:206
end

script.labels["BaseWanderStopTick"] = function(ctx)
    -- MONKGUARDBASIC.scr:209
    -- only do special wander if broom or hoe
    if ctx:condition("MONK_TYPE==1") then -- MONKGUARDBASIC.scr:212
        ctx:command("loopanim", "sAnimName, 0, DoNothing") -- MONKGUARDBASIC.scr:213
        -- <--------TL
        mm9.gosub(script, ctx, "Basewanderstart") -- MONKGUARDBASIC.scr:214
    else -- MONKGUARDBASIC.scr:215
        if ctx:condition("MONK_TYPE==2") then -- MONKGUARDBASIC.scr:216
            ctx:command("loopanim", "sAnimName, 0, DoNothing") -- MONKGUARDBASIC.scr:217
            -- <--------TL
            mm9.gosub(script, ctx, "Basewanderstart") -- MONKGUARDBASIC.scr:218
        else -- MONKGUARDBASIC.scr:219
            mm9.gosub(script, ctx, "BaseWanderStopTick") -- MONKGUARDBASIC.scr:220
        end -- MONKGUARDBASIC.scr:221
    end -- MONKGUARDBASIC.scr:222
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:224
end

script.labels["BaseWanderStart"] = function(ctx)
    -- MONKGUARDBASIC.scr:229
    -- TL
    -- Loop sPauseName in case
    -- we take a bit to start wandering
    ctx:command("loopanim", "sPauseName 0 Donothing") -- MONKGUARDBASIC.scr:235
    mm9.gosub(script, ctx, "BaseWanderStart") -- MONKGUARDBASIC.scr:237
    do return ctx:exit("") end -- MONKGUARDBASIC.scr:239
end

script.labels["BaseWanderObstacle"] = function(ctx)
    -- MONKGUARDBASIC.scr:242
    if ctx:condition("hCurrentMarker!=NULL") then -- MONKGUARDBASIC.scr:244
        do return ctx:exit("FALSE") end -- MONKGUARDBASIC.scr:245
    end -- MONKGUARDBASIC.scr:246
    ctx:command("getrandomint", "0, 100, g_nRandom") -- MONKGUARDBASIC.scr:248
    ctx:getParam(0, "g_hObject") -- MONKGUARDBASIC.scr:250
    ctx:command("isclass", "g_hObject,Actor, g_bTemp") -- MONKGUARDBASIC.scr:251
    if ctx:condition("g_bTemp==TRUE") then -- MONKGUARDBASIC.scr:253
        if ctx:condition("g_nRandom < 90") then -- MONKGUARDBASIC.scr:254
            do return ctx:exit("FALSE") end -- MONKGUARDBASIC.scr:255
        end -- MONKGUARDBASIC.scr:256
    else -- MONKGUARDBASIC.scr:257
        if ctx:condition("g_nRandom < 70") then -- MONKGUARDBASIC.scr:258
            do return ctx:exit("FALSE") end -- MONKGUARDBASIC.scr:259
        end -- MONKGUARDBASIC.scr:260
    end -- MONKGUARDBASIC.scr:261
    ctx:getParam(1, "normalX") -- MONKGUARDBASIC.scr:263
    ctx:getParam(2, "normalY") -- MONKGUARDBASIC.scr:264
    ctx:getParam(3, "normalZ") -- MONKGUARDBASIC.scr:265
    mm9.gosub(script, ctx, "BaseWanderPause") -- MONKGUARDBASIC.scr:267
    ctx:command("stop", "") -- MONKGUARDBASIC.scr:268
    ctx:command("loopanim", "sAnimName, 0 Donothing") -- MONKGUARDBASIC.scr:269
    ctx:command("wait", "WANDER_LEASH_WAIT, 0, DoNothing") -- MONKGUARDBASIC.scr:270
    ctx:command("bobstacle", "= TRUE") -- MONKGUARDBASIC.scr:271
    mm9.gosub(script, ctx, "BaseWanderResume") -- MONKGUARDBASIC.scr:272
    ctx:getParam(0, "g_hObject") -- MONKGUARDBASIC.scr:274
    ctx:command("isclass", "g_hObject,Actor, g_bTemp") -- MONKGUARDBASIC.scr:275
    if ctx:condition("g_bTemp==FALSE") then -- MONKGUARDBASIC.scr:276
        ctx:command("facedir", "normalX, 0, normalZ, 360") -- MONKGUARDBASIC.scr:277
    end -- MONKGUARDBASIC.scr:278
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:281
end

script.labels["BecomeHostile"] = function(ctx)
    -- MONKGUARDBASIC.scr:284
    -- detach tool before attacking
    mm9.gosub(script, ctx, "SafeDetach") -- MONKGUARDBASIC.scr:287
    mm9.gosub(script, ctx, "BecomeHostile") -- MONKGUARDBASIC.scr:288
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:290
end

script.labels["SafeDetach"] = function(ctx)
    -- MONKGUARDBASIC.scr:293
    -- safe = no crash
    if ctx:condition("hProp!=0") then -- MONKGUARDBASIC.scr:296
        ctx:command("detachprop", "hProp, FALSE") -- MONKGUARDBASIC.scr:297
        ctx:command("removeobject", "hProp") -- MONKGUARDBASIC.scr:298
        ctx:command("hprop", "= NULL") -- MONKGUARDBASIC.scr:299
    end -- MONKGUARDBASIC.scr:300
    do return ctx:exit("TRUE") end -- MONKGUARDBASIC.scr:302
end

return script
