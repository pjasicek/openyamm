-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WORKINGMONK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "basemelee.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "Monksounds.inc" }

-- WorkingMonk.scr
-- timmy
-- Makes Monks play working animations
-- 10/23
-- parameters:
-- p0 the name of the animation to play
-- p1 number of NPC to do
-- p2 the name of the object to face after completing dialog
script.labels["DoRUDEAnim"] = function(ctx)
    -- WORKINGMONK.scr:37
    do return ctx:exit("") end -- WORKINGMONK.scr:40
end

script.labels["OnUse"] = function(ctx)
    -- WORKINGMONK.scr:43
    if ctx:condition("NPC_ID!=NULL") then -- WORKINGMONK.scr:46
        ctx:command("set", "Talking, TRUE") -- WORKINGMONK.scr:47
        ctx:command("stop", "") -- WORKINGMONK.scr:48
        mm9.gosub(script, ctx, "BasewanderStop") -- WORKINGMONK.scr:49
        ctx:command("getmyhandle", "g_hmyobject") -- WORKINGMONK.scr:50
        ctx:command("getcurranim", "g_hmyobject g_ntemp") -- WORKINGMONK.scr:51
        ctx:command("getanimname", "g_hmyobject g_ntemp g_stemp") -- WORKINGMONK.scr:52
        -- cprint g_stemp
        -- if (g_stemp==Monk_Anim)
        ctx:command("playanim", "Fidget_Name, FidgetStand") -- WORKINGMONK.scr:55
        -- endif
        ctx:getParam(0, "g_hobject") -- WORKINGMONK.scr:57
        ctx:command("faceobject", "g_hobject 200 DoNothing") -- WORKINGMONK.scr:58
        ctx:command("pausewait", "-1") -- WORKINGMONK.scr:59
        ctx:doRude("NPC_ID") -- WORKINGMONK.scr:60
        do return ctx:exit("TRUE") end -- WORKINGMONK.scr:61
    end -- WORKINGMONK.scr:62
    do return ctx:exit("TRUE") end -- WORKINGMONK.scr:64
end

script.labels["FidgetStand"] = function(ctx)
    -- WORKINGMONK.scr:68
    ctx:command("loopanim", "Fidget_Stand 0 Donothing") -- WORKINGMONK.scr:72
    do return ctx:exit("TRUE") end -- WORKINGMONK.scr:74
end

script.labels["OnRude"] = function(ctx)
    -- WORKINGMONK.scr:77
    ctx:command("resumewait", "-1") -- WORKINGMONK.scr:81
    ctx:command("set", "talking, FALSE") -- WORKINGMONK.scr:82
    ctx:command("getobjecthandle", "Face_Object g_hobject2") -- WORKINGMONK.scr:83
    if ctx:condition("g_hobject2!=NULL") then -- WORKINGMONK.scr:85
        ctx:command("faceobject", "g_hobject2 200 DoNothing") -- WORKINGMONK.scr:86
    end -- WORKINGMONK.scr:87
    ctx:command("loopanim", "Monk_Anim, 0 Donothing") -- WORKINGMONK.scr:89
    if ctx:condition("bWanderEnabled==TRUE") then -- WORKINGMONK.scr:91
        mm9.gosub(script, ctx, "Basewanderstart") -- WORKINGMONK.scr:92
        do return ctx:exit("") end -- WORKINGMONK.scr:93
    end -- WORKINGMONK.scr:94
    do return ctx:exit("") end -- WORKINGMONK.scr:96
end

script.labels["OnDamage"] = function(ctx)
    -- WORKINGMONK.scr:100
    ctx:command("detachprop", "g_hobject2, false") -- WORKINGMONK.scr:104
    ctx:command("removeobject", "g_hobject2") -- WORKINGMONK.scr:105
    ctx:command("set", "Attacked, True") -- WORKINGMONK.scr:106
    mm9.gosub(script, ctx, "BaseInit") -- WORKINGMONK.scr:107
    do return ctx:exit("") end -- WORKINGMONK.scr:109
end

script.labels["SetupWork"] = function(ctx)
    -- WORKINGMONK.scr:112
    ctx:command("attachprop", "Prop_Name Skin_Name Socket_Name g_hobject2") -- WORKINGMONK.scr:114
    ctx:command("set", "Working, True") -- WORKINGMONK.scr:115
    ctx:command("loopanim", "Fidget_Stand,0,Donothing") -- WORKINGMONK.scr:117
    do return ctx:exit("") end -- WORKINGMONK.scr:119
end

script.labels["StartWork"] = function(ctx)
    -- WORKINGMONK.scr:122
    ctx:command("getrandomint", "1, 10, g_ntemp") -- WORKINGMONK.scr:125
    ctx:command("wait", "1 g_ntemp OnWorkStart") -- WORKINGMONK.scr:126
    do return ctx:exit("") end -- WORKINGMONK.scr:127
end

script.labels["OnWorkStart"] = function(ctx)
    -- WORKINGMONK.scr:130
    ctx:command("set", "Working, True") -- WORKINGMONK.scr:133
    ctx:command("wait", "1 500 Rest") -- WORKINGMONK.scr:134
    ctx:command("loopanim", "Monk_Anim 0 Donothing") -- WORKINGMONK.scr:135
    mm9.gosub(script, ctx, "BaseWanderInit") -- WORKINGMONK.scr:137
    do return ctx:exit("") end -- WORKINGMONK.scr:139
end

script.labels["Rest"] = function(ctx)
    -- WORKINGMONK.scr:142
    ctx:command("playanim", "Fidget_Name StartWork") -- WORKINGMONK.scr:145
    do return ctx:exit("") end -- WORKINGMONK.scr:146
end

script.labels["BaseWanderGo"] = function(ctx)
    -- WORKINGMONK.scr:149
    ctx:command("playanim", "Fidget_Name WanderGo") -- WORKINGMONK.scr:152
    do return ctx:exit("") end -- WORKINGMONK.scr:153
end

script.labels["WanderGo"] = function(ctx)
    -- WORKINGMONK.scr:156
    ctx:command("loopanim", "Fidget_Stand, 0 Donothing") -- WORKINGMONK.scr:159
    if ctx:condition("Talking==FALSE") then -- WORKINGMONK.scr:160
        mm9.gosub(script, ctx, "BaseWanderGo") -- WORKINGMONK.scr:161
        do return ctx:exit("") end -- WORKINGMONK.scr:162
    end -- WORKINGMONK.scr:163
    do return ctx:exit("") end -- WORKINGMONK.scr:164
end

script.labels["BaseWanderStopTick"] = function(ctx)
    -- WORKINGMONK.scr:167
    ctx:command("wait", "WANDER_LEASH_WAIT, 0, DoNothing") -- WORKINGMONK.scr:170
    ctx:command("stop", "") -- WORKINGMONK.scr:171
    ctx:command("loopanim", "Monk_Anim, 0 Donothing") -- WORKINGMONK.scr:172
    mm9.gosub(script, ctx, "BaseWanderStart") -- WORKINGMONK.scr:173
    do return ctx:exit("") end -- WORKINGMONK.scr:175
end

script.labels["BaseWanderObstacle"] = function(ctx)
    -- WORKINGMONK.scr:178
    if ctx:condition("hCurrentMarker!=NULL") then -- WORKINGMONK.scr:180
        do return ctx:exit("FALSE") end -- WORKINGMONK.scr:181
    end -- WORKINGMONK.scr:182
    ctx:command("getrandomint", "0, 100, g_nRandom") -- WORKINGMONK.scr:184
    ctx:getParam(0, "g_hObject") -- WORKINGMONK.scr:186
    ctx:command("isclass", "g_hObject,Actor, g_bTemp") -- WORKINGMONK.scr:187
    if ctx:condition("g_bTemp==TRUE") then -- WORKINGMONK.scr:189
        if ctx:condition("g_nRandom < 90") then -- WORKINGMONK.scr:190
            do return ctx:exit("FALSE") end -- WORKINGMONK.scr:191
        end -- WORKINGMONK.scr:192
    else -- WORKINGMONK.scr:193
        if ctx:condition("g_nRandom < 70") then -- WORKINGMONK.scr:194
            do return ctx:exit("FALSE") end -- WORKINGMONK.scr:195
        end -- WORKINGMONK.scr:196
    end -- WORKINGMONK.scr:197
    ctx:getParam(1, "normalX") -- WORKINGMONK.scr:199
    ctx:getParam(2, "normalY") -- WORKINGMONK.scr:200
    ctx:getParam(3, "normalZ") -- WORKINGMONK.scr:201
    mm9.gosub(script, ctx, "BaseWanderPause") -- WORKINGMONK.scr:203
    ctx:command("stop", "") -- WORKINGMONK.scr:204
    ctx:command("loopanim", "Monk_Anim, 0 Donothing") -- WORKINGMONK.scr:205
    ctx:command("wait", "WANDER_LEASH_WAIT, 0, DoNothing") -- WORKINGMONK.scr:206
    ctx:command("bobstacle", "= TRUE") -- WORKINGMONK.scr:207
    mm9.gosub(script, ctx, "BaseWanderResume") -- WORKINGMONK.scr:208
    ctx:getParam(0, "g_hObject") -- WORKINGMONK.scr:210
    ctx:command("isclass", "g_hObject,Actor, g_bTemp") -- WORKINGMONK.scr:211
    if ctx:condition("g_bTemp==FALSE") then -- WORKINGMONK.scr:212
        ctx:command("facedir", "normalX, 0, normalZ, 360") -- WORKINGMONK.scr:213
    end -- WORKINGMONK.scr:214
    do return ctx:exit("TRUE") end -- WORKINGMONK.scr:217
end

script.labels["WorkInit"] = function(ctx)
    -- WORKINGMONK.scr:220
    if ctx:condition("Monk_Anim==Hoe") then -- WORKINGMONK.scr:223
        ctx:command("set", "Prop_Name MonkHoe.ABC") -- WORKINGMONK.scr:224
        ctx:command("set", "Skin_Name MonkHoe.dtx") -- WORKINGMONK.scr:225
        ctx:command("set", "Socket_Name Hoe") -- WORKINGMONK.scr:226
        ctx:command("set", "Fidget_Name HoeFidget") -- WORKINGMONK.scr:227
        ctx:command("set", "Fidget_Stand Hoewait") -- WORKINGMONK.scr:228
        do return ctx:exit("") end -- WORKINGMONK.scr:229
    end -- WORKINGMONK.scr:230
    if ctx:condition("Monk_Anim==Sweep") then -- WORKINGMONK.scr:232
        ctx:command("set", "Prop_Name MonkBroom.ABC") -- WORKINGMONK.scr:233
        ctx:command("set", "Skin_Name MonkBroom.dtx") -- WORKINGMONK.scr:234
        ctx:command("set", "Socket_Name Broom") -- WORKINGMONK.scr:235
        ctx:command("set", "Fidget_Name sweepfidget") -- WORKINGMONK.scr:236
        ctx:command("set", "Fidget_Stand Sweepwait") -- WORKINGMONK.scr:237
        do return ctx:exit("") end -- WORKINGMONK.scr:238
    end -- WORKINGMONK.scr:239
    if ctx:condition("Monk_Anim==Hammer") then -- WORKINGMONK.scr:241
        ctx:command("set", "Prop_Name MonkHammer.ABC") -- WORKINGMONK.scr:242
        ctx:command("set", "Skin_Name MonkHammer.dtx") -- WORKINGMONK.scr:243
        ctx:command("set", "Socket_Name Hammer") -- WORKINGMONK.scr:244
        ctx:command("set", "Fidget_Name HammerFidget") -- WORKINGMONK.scr:245
        ctx:command("set", "Fidget_Stand Hammerwait") -- WORKINGMONK.scr:246
        do return ctx:exit("") end -- WORKINGMONK.scr:247
    end -- WORKINGMONK.scr:248
    if ctx:condition("Monk_Anim==Wash") then -- WORKINGMONK.scr:250
        ctx:command("set", "Prop_Name MonkCloth.ABC") -- WORKINGMONK.scr:251
        ctx:command("set", "Skin_Name MonkCloth.dtx") -- WORKINGMONK.scr:252
        ctx:command("set", "Socket_Name Cloth") -- WORKINGMONK.scr:253
        ctx:command("set", "Fidget_Name WashFidget") -- WORKINGMONK.scr:254
        ctx:command("set", "Fidget_Stand WashWait") -- WORKINGMONK.scr:255
        do return ctx:exit("") end -- WORKINGMONK.scr:256
    end -- WORKINGMONK.scr:257
    do return ctx:exit("") end -- WORKINGMONK.scr:259
end

script.labels["Init"] = function(ctx)
    -- WORKINGMONK.scr:263
    mm9.gosub(script, ctx, "WorkInit") -- WORKINGMONK.scr:266
    mm9.gosub(script, ctx, "SetupWork") -- WORKINGMONK.scr:267
    mm9.gosub(script, ctx, "StartWork") -- WORKINGMONK.scr:268
    mm9.gosub(script, ctx, "MS_Init") -- WORKINGMONK.scr:269
    do return ctx:exit("") end -- WORKINGMONK.scr:271
end

script.labels["Main"] = function(ctx)
    -- WORKINGMONK.scr:274
    ctx:getParam(0, "Monk_Anim") -- WORKINGMONK.scr:277
    ctx:getParam(1, "NPC_ID") -- WORKINGMONK.scr:278
    ctx:getParam(2, "Face_Object") -- WORKINGMONK.scr:279
    ctx:getParam(3, "bSoundOn") -- WORKINGMONK.scr:280
    ctx:addTrigger("Use", "Onuse") -- WORKINGMONK.scr:281
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- WORKINGMONK.scr:282
    ctx:command("ondamage", "OnDamage") -- WORKINGMONK.scr:283
    ctx:command("onpoststartworld", "Init") -- WORKINGMONK.scr:284
    -- jsl-->OnPostMiniSaveLoad Init
    -- jsl-->OnPostSaveLoad Init
    ctx:command("wait", "1 .1 Init") -- WORKINGMONK.scr:287
    do return ctx:exit("") end -- WORKINGMONK.scr:288
end

return script
