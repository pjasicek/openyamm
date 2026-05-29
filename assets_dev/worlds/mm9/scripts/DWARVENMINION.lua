-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DWARVENMINION.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 27, path = "globals.inc" }

-- DwarvenMinion.scr
-- by SJR/Ed Campos
-- 10-05-01
-- Purpose:mine an area and
-- follow the Foreman
-- (DwarvenMinerA will
-- only mine and return)
-- -DEDIT NOTES-
-- ScriptParams are:
-- p0 = First mining site
-- p1 = Second mining site
-- p2->p8 = in order waypoint names for traveling
-- to mining sites
-- p9 = Name of place to run to during "panic"
-- Miners will "panic" and run around
-- and start their emergency routine
-- when "FreakOut" is triggered
-- p10 = DwarvenForemanName
script.labels["InitDwarvenMinion"] = function(ctx)
    -- DWARVENMINION.scr:56
    ctx:addTrigger("FreakOut", "OnPanic") -- DWARVENMINION.scr:58
    ctx:addTrigger("NextSite", "OnNextSite") -- DWARVENMINION.scr:59
    ctx:state().hForeman = ctx:objectOrNil("sForemanName") -- DWARVENMINION.scr:61
    ctx:setCallback(0, "SetSite0") -- DWARVENMINION.scr:63
    ctx:setCallback(1, "SetSite1") -- DWARVENMINION.scr:64
    mm9.gosub(script, ctx, "StartMiningRaw") -- DWARVENMINION.scr:68
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:69
end

script.labels["StartMiningRaw"] = function(ctx)
    -- DWARVENMINION.scr:73
    ctx:state().hMineSite = ctx:objectOrNil("sSite0Name") -- DWARVENMINION.scr:76
    ctx:wait(0, .1, "GotoWaypoint4") -- DWARVENMINION.scr:77
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:79
end

script.labels["StartMining"] = function(ctx)
    -- DWARVENMINION.scr:82
    ctx:wait(0, .1, "GotoWaypoint0") -- DWARVENMINION.scr:85
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:87
end

script.labels["GotoWaypoint0"] = function(ctx)
    -- DWARVENMINION.scr:90
    ctx:state().nCurIndex = 0 -- DWARVENMINION.scr:92
    ctx:self():stop() -- DWARVENMINION.scr:93
    ctx:state().hWayPoint = ctx:objectOrNil("sWayPoint0Name") -- DWARVENMINION.scr:94
    ctx:self():walkTo(ctx:object("hWayPoint"), 10, "GotoWayPoint1") -- DWARVENMINION.scr:95
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:96
end

script.labels["GotoWaypoint1"] = function(ctx)
    -- DWARVENMINION.scr:99
    ctx:state().nCurIndex = 1 -- DWARVENMINION.scr:101
    ctx:self():stop() -- DWARVENMINION.scr:102
    ctx:state().hWayPoint = ctx:objectOrNil("sWayPoint1Name") -- DWARVENMINION.scr:103
    ctx:self():walkTo(ctx:object("hWayPoint"), 10, "GotoWayPoint2") -- DWARVENMINION.scr:104
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:105
end

script.labels["GotoWaypoint2"] = function(ctx)
    -- DWARVENMINION.scr:108
    ctx:state().nCurIndex = 2 -- DWARVENMINION.scr:110
    ctx:self():stop() -- DWARVENMINION.scr:111
    ctx:state().hWayPoint = ctx:objectOrNil("sWayPoint2Name") -- DWARVENMINION.scr:112
    ctx:self():walkTo(ctx:object("hWayPoint"), 10, "GotoWayPoint3") -- DWARVENMINION.scr:113
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:114
end

script.labels["GotoWaypoint3"] = function(ctx)
    -- DWARVENMINION.scr:117
    ctx:state().nCurIndex = 3 -- DWARVENMINION.scr:119
    ctx:self():stop() -- DWARVENMINION.scr:120
    ctx:state().hWayPoint = ctx:objectOrNil("sWayPoint3Name") -- DWARVENMINION.scr:121
    ctx:self():walkTo(ctx:object("hWayPoint"), 10, "GotoWayPoint4") -- DWARVENMINION.scr:122
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:123
end

script.labels["GotoWaypoint4"] = function(ctx)
    -- DWARVENMINION.scr:126
    ctx:state().nCurIndex = 4 -- DWARVENMINION.scr:128
    ctx:self():stop() -- DWARVENMINION.scr:129
    ctx:state().hWayPoint = ctx:objectOrNil("sWayPoint4Name") -- DWARVENMINION.scr:130
    ctx:self():walkTo(ctx:object("hWayPoint"), 10, "GotoWayPoint5") -- DWARVENMINION.scr:131
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:132
end

script.labels["GotoWaypoint5"] = function(ctx)
    -- DWARVENMINION.scr:135
    ctx:state().nCurIndex = 5 -- DWARVENMINION.scr:137
    ctx:self():stop() -- DWARVENMINION.scr:138
    ctx:state().hWayPoint = ctx:objectOrNil("sWayPoint5Name") -- DWARVENMINION.scr:139
    ctx:self():walkTo(ctx:object("hWayPoint"), 10, "GotoWayPoint6") -- DWARVENMINION.scr:140
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:141
end

script.labels["GotoWaypoint6"] = function(ctx)
    -- DWARVENMINION.scr:144
    ctx:state().nCurIndex = 6 -- DWARVENMINION.scr:146
    ctx:self():stop() -- DWARVENMINION.scr:147
    ctx:state().hWayPoint = ctx:objectOrNil("sWayPoint6Name") -- DWARVENMINION.scr:148
    ctx:self():walkTo(ctx:object("hWayPoint"), 10, "GotoMiningSpot") -- DWARVENMINION.scr:149
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:150
end

script.labels["GotoMiningSpot"] = function(ctx)
    -- DWARVENMINION.scr:153
    ctx:self():stop() -- DWARVENMINION.scr:155
    ctx:self():walkTo(ctx:object("hMineSite"), 10, "DoMining") -- DWARVENMINION.scr:156
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:157
end

script.labels["DoMining"] = function(ctx)
    -- DWARVENMINION.scr:160
    ctx:self():stop() -- DWARVENMINION.scr:162
    ctx:self():faceObject(ctx:object("hMineSite"), 180, "PlayMiningAnim") -- DWARVENMINION.scr:163
    -- Wait 0, 1, PlayMiningAnim
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:165
end

script.labels["PlayMiningAnim"] = function(ctx)
    -- DWARVENMINION.scr:168
    mm9.gosub(script, ctx, "PlayRandomSound") -- DWARVENMINION.scr:171
    ctx:self():playAnimation("HAttack1", "DoNothing") -- DWARVENMINION.scr:172
    ctx:wait(0, 1, "PlayMiningAnim") -- DWARVENMINION.scr:173
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:174
end

script.labels["OnNextSite"] = function(ctx)
    -- DWARVENMINION.scr:177
    ctx:self():stop() -- DWARVENMINION.scr:179
    ctx:wait(1, 3, "Lookup") -- DWARVENMINION.scr:181
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:182
end

script.labels["Lookup"] = function(ctx)
    -- DWARVENMINION.scr:185
    ctx:self():faceObject(ctx:object("hForeman"), 180, "DoNothing") -- DWARVENMINION.scr:188
    ctx:wait(0, 2, "ChangeSite") -- DWARVENMINION.scr:189
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:190
end

script.labels["OnPanic"] = function(ctx)
    -- DWARVENMINION.scr:193
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:195
end

script.labels["ChangeSite"] = function(ctx)
    -- DWARVENMINION.scr:198
    ctx:set("nCurSite", "nCurSite + 1") -- DWARVENMINION.scr:200
    ctx:mod("nCurSite", "MAXSites") -- DWARVENMINION.scr:201
    ctx:doCallback("nCurSite") -- DWARVENMINION.scr:202
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:203
end

script.labels["SetSite0"] = function(ctx)
    -- DWARVENMINION.scr:206
    ctx:state().hMineSite = ctx:objectOrNil("sSite0Name") -- DWARVENMINION.scr:208
    mm9.gosub(script, ctx, "ReverseWaypoints") -- DWARVENMINION.scr:209
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:210
end

script.labels["SetSite1"] = function(ctx)
    -- DWARVENMINION.scr:213
    ctx:state().hMineSite = ctx:objectOrNil("sSite1Name") -- DWARVENMINION.scr:215
    mm9.gosub(script, ctx, "ReverseWaypoints") -- DWARVENMINION.scr:216
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:217
end

script.labels["ReverseWaypoints"] = function(ctx)
    -- DWARVENMINION.scr:221
    -- Reverse path 0123456789=9876543210
    -- so we can go back after
    ctx:set("sTemp", "sWayPoint0Name") -- DWARVENMINION.scr:226
    ctx:set("sWayPoint0Name", "sWayPoint6Name") -- DWARVENMINION.scr:227
    ctx:set("sWayPoint6Name", "sTemp") -- DWARVENMINION.scr:228
    ctx:set("sTemp", "sWayPoint1Name") -- DWARVENMINION.scr:230
    ctx:set("sWayPoint1Name", "sWayPoint5Name") -- DWARVENMINION.scr:231
    ctx:set("sWayPoint5Name", "sTemp") -- DWARVENMINION.scr:232
    ctx:set("sTemp", "sWayPoint2Name") -- DWARVENMINION.scr:234
    ctx:set("sWayPoint2Name", "sWayPoint4Name") -- DWARVENMINION.scr:235
    ctx:set("sWayPoint4Name", "sTemp") -- DWARVENMINION.scr:236
    mm9.gosub(script, ctx, "StartMining") -- DWARVENMINION.scr:238
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:240
end

script.labels["KeepGoing"] = function(ctx)
    -- DWARVENMINION.scr:242
    ctx:self():stop() -- DWARVENMINION.scr:244
    if ctx:condition("nCurIndex==0") then -- DWARVENMINION.scr:246
        mm9.gosub(script, ctx, "GoToWaypoint0") -- DWARVENMINION.scr:247
        do return ctx:exit("TRUE") end -- DWARVENMINION.scr:248
    end -- DWARVENMINION.scr:249
    if ctx:condition("nCurIndex==1") then -- DWARVENMINION.scr:250
        mm9.gosub(script, ctx, "GoToWaypoint1") -- DWARVENMINION.scr:251
        do return ctx:exit("TRUE") end -- DWARVENMINION.scr:252
    end -- DWARVENMINION.scr:253
    if ctx:condition("nCurIndex==2") then -- DWARVENMINION.scr:254
        mm9.gosub(script, ctx, "GoToWaypoint2") -- DWARVENMINION.scr:255
        do return ctx:exit("TRUE") end -- DWARVENMINION.scr:256
    end -- DWARVENMINION.scr:257
    if ctx:condition("nCurIndex==3") then -- DWARVENMINION.scr:258
        mm9.gosub(script, ctx, "GoToWaypoint3") -- DWARVENMINION.scr:259
        do return ctx:exit("TRUE") end -- DWARVENMINION.scr:260
    end -- DWARVENMINION.scr:261
    if ctx:condition("nCurIndex==4") then -- DWARVENMINION.scr:262
        mm9.gosub(script, ctx, "GoToWaypoint4") -- DWARVENMINION.scr:263
        do return ctx:exit("TRUE") end -- DWARVENMINION.scr:264
    end -- DWARVENMINION.scr:265
    if ctx:condition("nCurIndex==5") then -- DWARVENMINION.scr:266
        mm9.gosub(script, ctx, "GoToWaypoint5") -- DWARVENMINION.scr:267
        do return ctx:exit("TRUE") end -- DWARVENMINION.scr:268
    end -- DWARVENMINION.scr:269
    if ctx:condition("nCurIndex==6") then -- DWARVENMINION.scr:270
        mm9.gosub(script, ctx, "GoToWaypoint6") -- DWARVENMINION.scr:271
        do return ctx:exit("TRUE") end -- DWARVENMINION.scr:272
    end -- DWARVENMINION.scr:273
    if ctx:condition("nCurIndex==7") then -- DWARVENMINION.scr:274
        mm9.gosub(script, ctx, "DoNothing") -- DWARVENMINION.scr:275
        do return ctx:exit("TRUE") end -- DWARVENMINION.scr:276
    end -- DWARVENMINION.scr:277
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:278
end

script.labels["PlayRandomSound"] = function(ctx)
    -- DWARVENMINION.scr:282
    ctx:randomInt(0, 2, "ranim") -- DWARVENMINION.scr:284
    if ctx:condition("ranim==0") then -- DWARVENMINION.scr:285
        ctx:playSound("sounds\\animsounds\\dwarfwattack1.wav", "OnSoundDone", "hSound", 5000, "FALSE", 100) -- DWARVENMINION.scr:286
    end -- DWARVENMINION.scr:287
    if ctx:condition("ranim==1") then -- DWARVENMINION.scr:288
        ctx:playSound("sounds\\animsounds\\dwarfwattack2.wav", "OnSoundDone", "hSound", 5000, "FALSE", 100) -- DWARVENMINION.scr:289
    end -- DWARVENMINION.scr:290
    if ctx:condition("ranim==2") then -- DWARVENMINION.scr:291
        ctx:playSound("sounds\\animsounds\\dwarfwince1.wav", "OnSoundDone", "hSound", 5000, "FALSE", 100) -- DWARVENMINION.scr:292
    end -- DWARVENMINION.scr:293
    ctx:randomInt(0, 2, "ranim") -- DWARVENMINION.scr:294
    if ctx:condition("ranim==0") then -- DWARVENMINION.scr:295
        ctx:playSound("sounds\\weapons\\bigswordclang.wav", "OnSoundDone", "hSound", 5000, "FALSE", 100) -- DWARVENMINION.scr:296
    end -- DWARVENMINION.scr:297
    if ctx:condition("ranim==1") then -- DWARVENMINION.scr:298
        ctx:playSound("sounds\\weapons\\battleaxethump.wav", "OnSoundDone", "hSound", 5000, "FALSE", 100) -- DWARVENMINION.scr:299
    end -- DWARVENMINION.scr:300
    if ctx:condition("ranim==2") then -- DWARVENMINION.scr:301
        ctx:playSound("sounds\\weapons\\carmorchain.wav", "OnSoundDone", "hSound", 5000, "FALSE", 100) -- DWARVENMINION.scr:302
    end -- DWARVENMINION.scr:303
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:304
end

script.labels["OnSoundDone"] = function(ctx)
    -- DWARVENMINION.scr:307
    ctx:killSound("hSound") -- DWARVENMINION.scr:309
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:310
end

script.labels["Main"] = function(ctx)
    -- DWARVENMINION.scr:312
    -- TraceOn
    ctx:getParam(0, "sSite0Name") -- DWARVENMINION.scr:317
    ctx:getParam(1, "sSite1Name") -- DWARVENMINION.scr:318
    ctx:getParam(2, "sWayPoint0Name") -- DWARVENMINION.scr:319
    ctx:getParam(3, "sWayPoint1Name") -- DWARVENMINION.scr:320
    ctx:getParam(4, "sWayPoint2Name") -- DWARVENMINION.scr:321
    ctx:getParam(5, "sWayPoint3Name") -- DWARVENMINION.scr:322
    ctx:getParam(6, "sWayPoint4Name") -- DWARVENMINION.scr:323
    ctx:getParam(7, "sWayPoint5Name") -- DWARVENMINION.scr:324
    ctx:getParam(8, "sWayPoint6Name") -- DWARVENMINION.scr:325
    ctx:getParam(9, "sBunkerName") -- DWARVENMINION.scr:326
    ctx:getParam(10, "sForemanName") -- DWARVENMINION.scr:327
    ctx:cacheSound("sounds\\pickupitems\\metal.wav") -- DWARVENMINION.scr:330
    ctx:cacheSound("sounds\\animsounds\\dwarfaware.wav") -- DWARVENMINION.scr:331
    ctx:cacheSound("sounds\\animsounds\\dwarfwattack1.wav") -- DWARVENMINION.scr:332
    ctx:wait(0, .1, "InitDwarvenMinion") -- DWARVENMINION.scr:334
    do return ctx:exit("TRUE") end -- DWARVENMINION.scr:335
end

return script
