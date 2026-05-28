-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_INTERROGATIONGUARD0.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseMelee.inc" }

-- DP_InterrogationGuard0.scr
-- kd
-- 10-21-01
-- Simple following guard
-- Nothing slick or fancy
script.labels["Directions"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:48
    ctx:command("ncount", "= nCount + 1") -- DP_INTERROGATIONGUARD0.scr:50
    if ctx:condition("nCount==1") then -- DP_INTERROGATIONGUARD0.scr:52
        mm9.gosub(script, ctx, "NextPrisoner") -- DP_INTERROGATIONGUARD0.scr:53
    else -- DP_INTERROGATIONGUARD0.scr:54
        if ctx:condition("nCount==2") then -- DP_INTERROGATIONGUARD0.scr:55
            mm9.gosub(script, ctx, "DoTheWalk") -- DP_INTERROGATIONGUARD0.scr:56
        else -- DP_INTERROGATIONGUARD0.scr:57
            if ctx:condition("nCount==3") then -- DP_INTERROGATIONGUARD0.scr:58
                mm9.gosub(script, ctx, "NextPrisoner") -- DP_INTERROGATIONGUARD0.scr:59
            else -- DP_INTERROGATIONGUARD0.scr:60
                if ctx:condition("nCount==4") then -- DP_INTERROGATIONGUARD0.scr:61
                    mm9.gosub(script, ctx, "DoTheWalk") -- DP_INTERROGATIONGUARD0.scr:62
                else -- DP_INTERROGATIONGUARD0.scr:63
                    if ctx:condition("nCount==5") then -- DP_INTERROGATIONGUARD0.scr:64
                        mm9.gosub(script, ctx, "NextPrisoner") -- DP_INTERROGATIONGUARD0.scr:65
                    else -- DP_INTERROGATIONGUARD0.scr:66
                        if ctx:condition("nCount==6") then -- DP_INTERROGATIONGUARD0.scr:67
                            ctx:command("ncount", "= 0") -- DP_INTERROGATIONGUARD0.scr:68
                            mm9.gosub(script, ctx, "DoTheWalk") -- DP_INTERROGATIONGUARD0.scr:69
                        end -- DP_INTERROGATIONGUARD0.scr:70
                    end -- DP_INTERROGATIONGUARD0.scr:71
                end -- DP_INTERROGATIONGUARD0.scr:72
            end -- DP_INTERROGATIONGUARD0.scr:73
        end -- DP_INTERROGATIONGUARD0.scr:74
    end -- DP_INTERROGATIONGUARD0.scr:75
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:76
end

script.labels["WalkToLastMarker"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:78
    if ctx:condition("nNumA==1") then -- DP_INTERROGATIONGUARD0.scr:80
        ctx:command("nmarker", "= nMarker + 1") -- DP_INTERROGATIONGUARD0.scr:81
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONGUARD0.scr:82
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONGUARD0.scr:83
        ctx:command("hcelldoor", "= NULL") -- DP_INTERROGATIONGUARD0.scr:84
        ctx:command("getobjecthandle", "sCellDoorA, hCellDoor") -- DP_INTERROGATIONGUARD0.scr:85
        ctx:command("walkto", "hMarker 10 Cell") -- DP_INTERROGATIONGUARD0.scr:86
    end -- DP_INTERROGATIONGUARD0.scr:87
    if ctx:condition("nNumA==2") then -- DP_INTERROGATIONGUARD0.scr:88
        ctx:command("nmarker", "= nMarker + 2") -- DP_INTERROGATIONGUARD0.scr:89
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONGUARD0.scr:90
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONGUARD0.scr:91
        ctx:command("hcelldoor", "= NULL") -- DP_INTERROGATIONGUARD0.scr:92
        ctx:command("getobjecthandle", "sCellDoorB, hCellDoor") -- DP_INTERROGATIONGUARD0.scr:93
        ctx:command("walkto", "hMarker 10 Cell") -- DP_INTERROGATIONGUARD0.scr:94
    end -- DP_INTERROGATIONGUARD0.scr:95
    if ctx:condition("nNumA==3") then -- DP_INTERROGATIONGUARD0.scr:96
        ctx:command("nmarker", "= nMarker + 3") -- DP_INTERROGATIONGUARD0.scr:97
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONGUARD0.scr:98
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONGUARD0.scr:99
        ctx:command("hcelldoor", "= NULL") -- DP_INTERROGATIONGUARD0.scr:100
        ctx:command("getobjecthandle", "sCellDoorC, hCellDoor") -- DP_INTERROGATIONGUARD0.scr:101
        ctx:command("walkto", "hMarker 10 Cell") -- DP_INTERROGATIONGUARD0.scr:102
    end -- DP_INTERROGATIONGUARD0.scr:103
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:104
end

script.labels["DoTheWalk"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:109
    ctx:command("nreset", "= nReset + 1") -- DP_INTERROGATIONGUARD0.scr:111
    ctx:command("cprint", "\"DoTheWalk\"") -- DP_INTERROGATIONGUARD0.scr:112
    ctx:command("cprint", "nReset") -- DP_INTERROGATIONGUARD0.scr:113
    if ctx:condition("nVarPath==0") then -- DP_INTERROGATIONGUARD0.scr:114
        ctx:command("nvarpath", "= 1") -- DP_INTERROGATIONGUARD0.scr:115
        ctx:command("nnuma", "= nNumA + 1") -- DP_INTERROGATIONGUARD0.scr:116
        mm9.gosub(script, ctx, "ToTheWarden") -- DP_INTERROGATIONGUARD0.scr:117
    else -- DP_INTERROGATIONGUARD0.scr:118
        ctx:command("nvarpath", "= 0") -- DP_INTERROGATIONGUARD0.scr:119
        mm9.gosub(script, ctx, "ToTheInterrogation") -- DP_INTERROGATIONGUARD0.scr:121
    end -- DP_INTERROGATIONGUARD0.scr:122
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:125
end

script.labels["ToTheWarden"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:128
    if ctx:condition("nMarker == 0") then -- DP_INTERROGATIONGUARD0.scr:131
        ctx:command("playsound", "Sounds\\Door\\doorslammetal02.wav, DoNothing, hDummy, 5000, FALSE, 100") -- DP_INTERROGATIONGUARD0.scr:133
        ctx:command("wait", "0, .3, DoNothing") -- DP_INTERROGATIONGUARD0.scr:134
        ctx:trigger("hDoorMan", "UnlockRoom") -- DP_INTERROGATIONGUARD0.scr:135
    end -- DP_INTERROGATIONGUARD0.scr:136
    if ctx:condition("nMarker < nNumMarkers") then -- DP_INTERROGATIONGUARD0.scr:138
        ctx:command("nmarker", "= nMarker + 1") -- DP_INTERROGATIONGUARD0.scr:139
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONGUARD0.scr:140
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONGUARD0.scr:141
        ctx:command("walkto", "hMarker 10 ToTheWarden") -- DP_INTERROGATIONGUARD0.scr:142
    else -- DP_INTERROGATIONGUARD0.scr:143
        mm9.gosub(script, ctx, "WalkToLastMarker") -- DP_INTERROGATIONGUARD0.scr:144
    end -- DP_INTERROGATIONGUARD0.scr:145
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:147
end

script.labels["ToTheInterrogation"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:149
    if ctx:condition("nMarker != 0") then -- DP_INTERROGATIONGUARD0.scr:152
        ctx:command("nmarker", "= nMarker - 1") -- DP_INTERROGATIONGUARD0.scr:153
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONGUARD0.scr:154
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONGUARD0.scr:155
        ctx:command("walkto", "hMarker 10 ToTheInterrogation") -- DP_INTERROGATIONGUARD0.scr:156
    else -- DP_INTERROGATIONGUARD0.scr:157
        mm9.gosub(script, ctx, "InterrogationRoom") -- DP_INTERROGATIONGUARD0.scr:158
    end -- DP_INTERROGATIONGUARD0.scr:159
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:161
end

script.labels["InterrogationRoom"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:164
    if ctx:condition("nReset==6") then -- DP_INTERROGATIONGUARD0.scr:166
        ctx:command("nreset", "= 0") -- DP_INTERROGATIONGUARD0.scr:167
        ctx:command("stop", "") -- DP_INTERROGATIONGUARD0.scr:168
    else -- DP_INTERROGATIONGUARD0.scr:169
        ctx:command("nmarker", "= 0") -- DP_INTERROGATIONGUARD0.scr:170
        ctx:trigger("hDoorMan", "LockRoom") -- DP_INTERROGATIONGUARD0.scr:171
        ctx:command("stop", "") -- DP_INTERROGATIONGUARD0.scr:172
        ctx:command("playanim", "Aware, DoNothing") -- DP_INTERROGATIONGUARD0.scr:173
        ctx:command("playsound", "sounds\\BeatdownMixChained_8.wav, DoNothing, 100, 500, FALSE, 90") -- DP_INTERROGATIONGUARD0.scr:174
        ctx:command("wait", "1, 15, DoTheWalk") -- DP_INTERROGATIONGUARD0.scr:175
    end -- DP_INTERROGATIONGUARD0.scr:176
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:179
end

script.labels["NextPrisoner"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:183
    ctx:trigger("hWarden", "ChangeCell") -- DP_INTERROGATIONGUARD0.scr:185
    if ctx:condition("nNumA==1") then -- DP_INTERROGATIONGUARD0.scr:187
        ctx:command("nmarker", "= nMarker + 1") -- DP_INTERROGATIONGUARD0.scr:188
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONGUARD0.scr:189
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONGUARD0.scr:190
        ctx:command("nmarker", "= 4") -- DP_INTERROGATIONGUARD0.scr:191
        ctx:command("hcelldoor", "= NULL") -- DP_INTERROGATIONGUARD0.scr:192
        ctx:command("getobjecthandle", "sCellDoorB, hCellDoor") -- DP_INTERROGATIONGUARD0.scr:193
        ctx:command("walkto", "hMarker 10 Cell") -- DP_INTERROGATIONGUARD0.scr:194
    end -- DP_INTERROGATIONGUARD0.scr:195
    if ctx:condition("nNumA==2") then -- DP_INTERROGATIONGUARD0.scr:197
        ctx:command("nmarker", "= nMarker + 1") -- DP_INTERROGATIONGUARD0.scr:198
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONGUARD0.scr:199
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONGUARD0.scr:200
        ctx:command("nmarker", "= 4") -- DP_INTERROGATIONGUARD0.scr:201
        ctx:command("hcelldoor", "= NULL") -- DP_INTERROGATIONGUARD0.scr:202
        ctx:command("getobjecthandle", "sCellDoorC, hCellDoor") -- DP_INTERROGATIONGUARD0.scr:203
        ctx:command("walkto", "hMarker 10 Cell") -- DP_INTERROGATIONGUARD0.scr:204
    end -- DP_INTERROGATIONGUARD0.scr:205
    if ctx:condition("nNumA==3") then -- DP_INTERROGATIONGUARD0.scr:207
        ctx:command("nmarker", "= nMarker - 2") -- DP_INTERROGATIONGUARD0.scr:208
        ctx:command("smarker", "= sWayPoint + nMarker") -- DP_INTERROGATIONGUARD0.scr:209
        ctx:command("getobjecthandle", "sMarker hMarker") -- DP_INTERROGATIONGUARD0.scr:210
        ctx:command("nmarker", "= 4") -- DP_INTERROGATIONGUARD0.scr:211
        ctx:command("hcelldoor", "= NULL") -- DP_INTERROGATIONGUARD0.scr:212
        ctx:command("getobjecthandle", "sCellDoorA, hCellDoor") -- DP_INTERROGATIONGUARD0.scr:213
        ctx:command("nnuma", "= 0") -- DP_INTERROGATIONGUARD0.scr:214
        ctx:command("walkto", "hMarker 10 Cell") -- DP_INTERROGATIONGUARD0.scr:215
    end -- DP_INTERROGATIONGUARD0.scr:216
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:219
end

script.labels["Cell"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:222
    ctx:command("stop", "") -- DP_INTERROGATIONGUARD0.scr:224
    ctx:trigger("hWarden", "OpenCell") -- DP_INTERROGATIONGUARD0.scr:225
    ctx:command("wait", "1, 2, DoNothing") -- DP_INTERROGATIONGUARD0.scr:226
    ctx:command("playanim", "Fidget1, DoNothing") -- DP_INTERROGATIONGUARD0.scr:227
    ctx:command("faceobject", "hCellDoor, 220, DoNothing") -- DP_INTERROGATIONGUARD0.scr:228
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:230
end

script.labels["CheckPlayer"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:233
    ctx:getParam(0, "hParam") -- DP_INTERROGATIONGUARD0.scr:235
    ctx:command("isplayer", "hParam, bIsPlayer") -- DP_INTERROGATIONGUARD0.scr:236
    ctx:hasKey(5007, "bHasFriendlyKey") -- DP_INTERROGATIONGUARD0.scr:237
    ctx:hasKey(5006, "bHasHostileKey") -- DP_INTERROGATIONGUARD0.scr:238
    ctx:command("bhashostilekey", "= 1 - bHasHostileKey") -- DP_INTERROGATIONGUARD0.scr:239
    ctx:command("bresult", "= bHasFriendlyKey * bHasHostileKey * bIsPlayer") -- DP_INTERROGATIONGUARD0.scr:240
    if ctx:condition("bResult == FALSE") then -- DP_INTERROGATIONGUARD0.scr:241
        ctx:giveKey(5006) -- DP_INTERROGATIONGUARD0.scr:242
        mm9.gosub(script, ctx, "AlertCall") -- DP_INTERROGATIONGUARD0.scr:243
    else -- DP_INTERROGATIONGUARD0.scr:244
        ctx:command("addfriend", "Player") -- DP_INTERROGATIONGUARD0.scr:245
    end -- DP_INTERROGATIONGUARD0.scr:246
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:248
end

script.labels["SetKeyValue"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:250
    ctx:getParam(0, "hParam") -- DP_INTERROGATIONGUARD0.scr:252
    ctx:command("isplayer", "hParam, bIsPlayer") -- DP_INTERROGATIONGUARD0.scr:253
    if ctx:condition("blsPlayer==TRUE") then -- DP_INTERROGATIONGUARD0.scr:254
        ctx:giveKey(5006) -- DP_INTERROGATIONGUARD0.scr:255
        ctx:command("removefriend", "Player") -- DP_INTERROGATIONGUARD0.scr:256
        mm9.gosub(script, ctx, "AlertCall") -- DP_INTERROGATIONGUARD0.scr:257
    else -- DP_INTERROGATIONGUARD0.scr:258
        ctx:command("addfriend", "Player") -- DP_INTERROGATIONGUARD0.scr:259
        mm9.gosub(script, ctx, "baseinit") -- DP_INTERROGATIONGUARD0.scr:260
    end -- DP_INTERROGATIONGUARD0.scr:261
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:262
end

script.labels["AlertCall"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:264
    if ctx:condition("sMyGuard==Interrogator0") then -- DP_INTERROGATIONGUARD0.scr:266
        ctx:command("playsound", "sounds\\VO\\Charrrge.wav, DoNothing, 100, 500, FALSE, 90") -- DP_INTERROGATIONGUARD0.scr:267
    else -- DP_INTERROGATIONGUARD0.scr:268
        ctx:command("playsound", "sounds\\VO\\TheyAreHere.wav, DoNothing, 100, 500, FALSE, 90") -- DP_INTERROGATIONGUARD0.scr:269
    end -- DP_INTERROGATIONGUARD0.scr:270
    ctx:command("runto", "hParam, 25, BaseInit") -- DP_INTERROGATIONGUARD0.scr:271
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:272
end

script.labels["Main2"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:275
    ctx:command("getobjecthandle", "InterrDoorman, hDoorMan") -- DP_INTERROGATIONGUARD0.scr:277
    ctx:command("getobjecthandle", "InterrWarden, hWarden") -- DP_INTERROGATIONGUARD0.scr:278
    ctx:command("nvarpath", "= 0") -- DP_INTERROGATIONGUARD0.scr:279
    ctx:command("nnummarkers", "= nNumMarkers - 2") -- DP_INTERROGATIONGUARD0.scr:280
    ctx:addTrigger("LetsGo", "DoTheWalk") -- DP_INTERROGATIONGUARD0.scr:282
    ctx:addTrigger("Start", "InterrogationRoom") -- DP_INTERROGATIONGUARD0.scr:283
    ctx:addTrigger("NextCell", "Directions") -- DP_INTERROGATIONGUARD0.scr:284
    ctx:command("onfoundtarget", "CheckPlayer") -- DP_INTERROGATIONGUARD0.scr:285
    ctx:command("ondamage", "SetKeyValue") -- DP_INTERROGATIONGUARD0.scr:286
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:288
end

script.labels["Main"] = function(ctx)
    -- DP_INTERROGATIONGUARD0.scr:291
    ctx:command("addfriend", "PrisonerHumanMaleA") -- DP_INTERROGATIONGUARD0.scr:293
    ctx:getParam(0, "sWayPoint") -- DP_INTERROGATIONGUARD0.scr:294
    ctx:getParam(1, "nNumMarkers") -- DP_INTERROGATIONGUARD0.scr:295
    ctx:getParam(2, "sCellDoorA") -- DP_INTERROGATIONGUARD0.scr:296
    ctx:getParam(3, "sCellDoorB") -- DP_INTERROGATIONGUARD0.scr:297
    ctx:getParam(4, "sCellDoorC") -- DP_INTERROGATIONGUARD0.scr:298
    ctx:getParam(5, "sMyGuard") -- DP_INTERROGATIONGUARD0.scr:299
    ctx:command("wait", "0 .1 main2") -- DP_INTERROGATIONGUARD0.scr:301
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD0.scr:303
end

return script
