-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DP_INTERROGATIONGUARD1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "BaseMelee.inc" }

-- DP_InterrogationGuard1.scr
-- kd
-- 10-21-01
-- Simple following guard
-- Nothing slick or fancy
script.labels["Directions"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:48
    ctx:set("nCount", "nCount + 1") -- DP_INTERROGATIONGUARD1.scr:50
    if ctx:condition("nCount==1") then -- DP_INTERROGATIONGUARD1.scr:52
        mm9.gosub(script, ctx, "NextPrisoner") -- DP_INTERROGATIONGUARD1.scr:53
    else -- DP_INTERROGATIONGUARD1.scr:54
        if ctx:condition("nCount==2") then -- DP_INTERROGATIONGUARD1.scr:55
            mm9.gosub(script, ctx, "DoTheWalk") -- DP_INTERROGATIONGUARD1.scr:56
        else -- DP_INTERROGATIONGUARD1.scr:57
            if ctx:condition("nCount==3") then -- DP_INTERROGATIONGUARD1.scr:58
                mm9.gosub(script, ctx, "NextPrisoner") -- DP_INTERROGATIONGUARD1.scr:59
            else -- DP_INTERROGATIONGUARD1.scr:60
                if ctx:condition("nCount==4") then -- DP_INTERROGATIONGUARD1.scr:61
                    mm9.gosub(script, ctx, "DoTheWalk") -- DP_INTERROGATIONGUARD1.scr:62
                else -- DP_INTERROGATIONGUARD1.scr:63
                    if ctx:condition("nCount==5") then -- DP_INTERROGATIONGUARD1.scr:64
                        mm9.gosub(script, ctx, "NextPrisoner") -- DP_INTERROGATIONGUARD1.scr:65
                    else -- DP_INTERROGATIONGUARD1.scr:66
                        if ctx:condition("nCount==6") then -- DP_INTERROGATIONGUARD1.scr:67
                            ctx:state().nCount = 0 -- DP_INTERROGATIONGUARD1.scr:68
                            mm9.gosub(script, ctx, "DoTheWalk") -- DP_INTERROGATIONGUARD1.scr:69
                        end -- DP_INTERROGATIONGUARD1.scr:70
                    end -- DP_INTERROGATIONGUARD1.scr:71
                end -- DP_INTERROGATIONGUARD1.scr:72
            end -- DP_INTERROGATIONGUARD1.scr:73
        end -- DP_INTERROGATIONGUARD1.scr:74
    end -- DP_INTERROGATIONGUARD1.scr:75
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:76
end

script.labels["WalkToLastMarker"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:78
    if ctx:condition("nNumA==1") then -- DP_INTERROGATIONGUARD1.scr:80
        ctx:set("nMarker", "nMarker + 1") -- DP_INTERROGATIONGUARD1.scr:81
        ctx:set("sMarker", "sWayPoint + nMarker") -- DP_INTERROGATIONGUARD1.scr:82
        ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_INTERROGATIONGUARD1.scr:83
        ctx:state().hCellDoor = nil -- DP_INTERROGATIONGUARD1.scr:84
        ctx:state().hCellDoor = ctx:objectOrNil("sCellDoorA") -- DP_INTERROGATIONGUARD1.scr:85
        ctx:self():walkTo(ctx:object("hMarker"), 10, "Cell") -- DP_INTERROGATIONGUARD1.scr:86
    end -- DP_INTERROGATIONGUARD1.scr:87
    if ctx:condition("nNumA==2") then -- DP_INTERROGATIONGUARD1.scr:88
        ctx:set("nMarker", "nMarker + 2") -- DP_INTERROGATIONGUARD1.scr:89
        ctx:set("sMarker", "sWayPoint + nMarker") -- DP_INTERROGATIONGUARD1.scr:90
        ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_INTERROGATIONGUARD1.scr:91
        ctx:state().hCellDoor = nil -- DP_INTERROGATIONGUARD1.scr:92
        ctx:state().hCellDoor = ctx:objectOrNil("sCellDoorB") -- DP_INTERROGATIONGUARD1.scr:93
        ctx:self():walkTo(ctx:object("hMarker"), 10, "Cell") -- DP_INTERROGATIONGUARD1.scr:94
    end -- DP_INTERROGATIONGUARD1.scr:95
    if ctx:condition("nNumA==3") then -- DP_INTERROGATIONGUARD1.scr:96
        ctx:set("nMarker", "nMarker + 3") -- DP_INTERROGATIONGUARD1.scr:97
        ctx:set("sMarker", "sWayPoint + nMarker") -- DP_INTERROGATIONGUARD1.scr:98
        ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_INTERROGATIONGUARD1.scr:99
        ctx:state().hCellDoor = nil -- DP_INTERROGATIONGUARD1.scr:100
        ctx:state().hCellDoor = ctx:objectOrNil("sCellDoorC") -- DP_INTERROGATIONGUARD1.scr:101
        ctx:self():walkTo(ctx:object("hMarker"), 10, "Cell") -- DP_INTERROGATIONGUARD1.scr:102
    end -- DP_INTERROGATIONGUARD1.scr:103
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:104
end

script.labels["DoTheWalk"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:109
    ctx:set("nReset", "nReset + 1") -- DP_INTERROGATIONGUARD1.scr:111
    if ctx:condition("nVarPath==0") then -- DP_INTERROGATIONGUARD1.scr:112
        ctx:state().nVarPath = 1 -- DP_INTERROGATIONGUARD1.scr:113
        ctx:set("nNumA", "nNumA + 1") -- DP_INTERROGATIONGUARD1.scr:114
        mm9.gosub(script, ctx, "ToTheWarden") -- DP_INTERROGATIONGUARD1.scr:115
    else -- DP_INTERROGATIONGUARD1.scr:116
        ctx:state().nVarPath = 0 -- DP_INTERROGATIONGUARD1.scr:117
        mm9.gosub(script, ctx, "ToTheInterrogation") -- DP_INTERROGATIONGUARD1.scr:119
    end -- DP_INTERROGATIONGUARD1.scr:120
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:123
end

script.labels["ToTheWarden"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:126
    if ctx:condition("nMarker < nNumMarkers") then -- DP_INTERROGATIONGUARD1.scr:129
        ctx:set("nMarker", "nMarker + 1") -- DP_INTERROGATIONGUARD1.scr:130
        ctx:set("sMarker", "sWayPoint + nMarker") -- DP_INTERROGATIONGUARD1.scr:131
        ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_INTERROGATIONGUARD1.scr:132
        ctx:self():walkTo(ctx:object("hMarker"), 10, "ToTheWarden") -- DP_INTERROGATIONGUARD1.scr:133
    else -- DP_INTERROGATIONGUARD1.scr:134
        mm9.gosub(script, ctx, "WalkToLastMarker") -- DP_INTERROGATIONGUARD1.scr:135
    end -- DP_INTERROGATIONGUARD1.scr:136
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:138
end

script.labels["ToTheInterrogation"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:140
    if ctx:condition("nMarker != 0") then -- DP_INTERROGATIONGUARD1.scr:142
        ctx:set("nMarker", "nMarker - 1") -- DP_INTERROGATIONGUARD1.scr:143
        ctx:set("sMarker", "sWayPoint + nMarker") -- DP_INTERROGATIONGUARD1.scr:144
        ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_INTERROGATIONGUARD1.scr:145
        if ctx:condition("nMarker == 1") then -- DP_INTERROGATIONGUARD1.scr:147
            ctx:trigger("hDoorMan", "UnlockRoom") -- DP_INTERROGATIONGUARD1.scr:148
        end -- DP_INTERROGATIONGUARD1.scr:149
        ctx:self():walkTo(ctx:object("hMarker"), 10, "ToTheInterrogation") -- DP_INTERROGATIONGUARD1.scr:151
    else -- DP_INTERROGATIONGUARD1.scr:152
        mm9.gosub(script, ctx, "InterrogationRoom") -- DP_INTERROGATIONGUARD1.scr:153
    end -- DP_INTERROGATIONGUARD1.scr:154
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:156
end

script.labels["InterrogationRoom"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:159
    if ctx:condition("nReset==6") then -- DP_INTERROGATIONGUARD1.scr:161
        ctx:state().nReset = 0 -- DP_INTERROGATIONGUARD1.scr:162
        ctx:self():stop() -- DP_INTERROGATIONGUARD1.scr:163
    else -- DP_INTERROGATIONGUARD1.scr:164
        ctx:state().nMarker = 0 -- DP_INTERROGATIONGUARD1.scr:165
        ctx:self():stop() -- DP_INTERROGATIONGUARD1.scr:166
        ctx:self():playAnimation("Aware", "DoNothing") -- DP_INTERROGATIONGUARD1.scr:167
        ctx:wait(1, 15, "DoTheWalk") -- DP_INTERROGATIONGUARD1.scr:168
    end -- DP_INTERROGATIONGUARD1.scr:169
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:171
end

script.labels["NextPrisoner"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:176
    if ctx:condition("nNumA==1") then -- DP_INTERROGATIONGUARD1.scr:178
        ctx:set("nMarker", "nMarker + 1") -- DP_INTERROGATIONGUARD1.scr:179
        ctx:set("sMarker", "sWayPoint + nMarker") -- DP_INTERROGATIONGUARD1.scr:180
        ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_INTERROGATIONGUARD1.scr:181
        ctx:state().nMarker = 4 -- DP_INTERROGATIONGUARD1.scr:182
        ctx:state().hCellDoor = nil -- DP_INTERROGATIONGUARD1.scr:183
        ctx:state().hCellDoor = ctx:objectOrNil("sCellDoorB") -- DP_INTERROGATIONGUARD1.scr:184
        ctx:self():walkTo(ctx:object("hMarker"), 10, "Cell") -- DP_INTERROGATIONGUARD1.scr:185
    end -- DP_INTERROGATIONGUARD1.scr:186
    if ctx:condition("nNumA==2") then -- DP_INTERROGATIONGUARD1.scr:188
        ctx:set("nMarker", "nMarker + 1") -- DP_INTERROGATIONGUARD1.scr:189
        ctx:set("sMarker", "sWayPoint + nMarker") -- DP_INTERROGATIONGUARD1.scr:190
        ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_INTERROGATIONGUARD1.scr:191
        ctx:state().nMarker = 4 -- DP_INTERROGATIONGUARD1.scr:192
        ctx:state().hCellDoor = nil -- DP_INTERROGATIONGUARD1.scr:193
        ctx:state().hCellDoor = ctx:objectOrNil("sCellDoorC") -- DP_INTERROGATIONGUARD1.scr:194
        ctx:self():walkTo(ctx:object("hMarker"), 10, "Cell") -- DP_INTERROGATIONGUARD1.scr:195
    end -- DP_INTERROGATIONGUARD1.scr:196
    if ctx:condition("nNumA==3") then -- DP_INTERROGATIONGUARD1.scr:198
        ctx:set("nMarker", "nMarker - 2") -- DP_INTERROGATIONGUARD1.scr:199
        ctx:set("sMarker", "sWayPoint + nMarker") -- DP_INTERROGATIONGUARD1.scr:200
        ctx:state().hMarker = ctx:objectOrNil("sMarker") -- DP_INTERROGATIONGUARD1.scr:201
        ctx:state().nMarker = 4 -- DP_INTERROGATIONGUARD1.scr:202
        ctx:state().hCellDoor = nil -- DP_INTERROGATIONGUARD1.scr:203
        ctx:state().hCellDoor = ctx:objectOrNil("sCellDoorA") -- DP_INTERROGATIONGUARD1.scr:204
        ctx:state().nNumA = 0 -- DP_INTERROGATIONGUARD1.scr:205
        ctx:self():walkTo(ctx:object("hMarker"), 10, "Cell") -- DP_INTERROGATIONGUARD1.scr:206
    end -- DP_INTERROGATIONGUARD1.scr:207
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:210
end

script.labels["Cell"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:212
    ctx:self():stop() -- DP_INTERROGATIONGUARD1.scr:214
    ctx:wait(1, 2, "DoNothing") -- DP_INTERROGATIONGUARD1.scr:215
    ctx:self():playAnimation("Fidget1", "DoNothing") -- DP_INTERROGATIONGUARD1.scr:216
    ctx:self():faceObject(ctx:object("hCellDoor"), 220, "DoNothing") -- DP_INTERROGATIONGUARD1.scr:217
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:219
end

script.labels["CheckPlayer"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:221
    ctx:getParam(0, "hParam") -- DP_INTERROGATIONGUARD1.scr:223
    ctx:state().bIsPlayer = ctx:object("hParam"):isPlayer() -- DP_INTERROGATIONGUARD1.scr:224
    ctx:hasKey(5007, "bHasFriendlyKey") -- DP_INTERROGATIONGUARD1.scr:225
    ctx:hasKey(5006, "bHasHostileKey") -- DP_INTERROGATIONGUARD1.scr:226
    ctx:set("bHasHostileKey", "1 - bHasHostileKey") -- DP_INTERROGATIONGUARD1.scr:227
    ctx:set("bResult", "bHasFriendlyKey * bHasHostileKey * bIsPlayer") -- DP_INTERROGATIONGUARD1.scr:228
    if ctx:condition("bResult == FALSE") then -- DP_INTERROGATIONGUARD1.scr:229
        ctx:giveKey(5006) -- DP_INTERROGATIONGUARD1.scr:230
        mm9.gosub(script, ctx, "AlertCall") -- DP_INTERROGATIONGUARD1.scr:231
    else -- DP_INTERROGATIONGUARD1.scr:232
        ctx:self():addFriend("Player") -- DP_INTERROGATIONGUARD1.scr:233
    end -- DP_INTERROGATIONGUARD1.scr:234
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:236
end

script.labels["SetKeyValue"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:238
    ctx:getParam(0, "hParam") -- DP_INTERROGATIONGUARD1.scr:240
    ctx:state().bIsPlayer = ctx:object("hParam"):isPlayer() -- DP_INTERROGATIONGUARD1.scr:241
    if ctx:condition("blsPlayer==TRUE") then -- DP_INTERROGATIONGUARD1.scr:242
        ctx:giveKey(5006) -- DP_INTERROGATIONGUARD1.scr:243
        ctx:self():removeFriend("Player") -- DP_INTERROGATIONGUARD1.scr:244
        mm9.gosub(script, ctx, "AlertCall") -- DP_INTERROGATIONGUARD1.scr:245
    else -- DP_INTERROGATIONGUARD1.scr:246
        ctx:self():addFriend("Player") -- DP_INTERROGATIONGUARD1.scr:247
        mm9.gosub(script, ctx, "baseinit") -- DP_INTERROGATIONGUARD1.scr:248
    end -- DP_INTERROGATIONGUARD1.scr:249
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:250
end

script.labels["AlertCall"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:252
    if ctx:condition("sMyGuard==Interrogator0") then -- DP_INTERROGATIONGUARD1.scr:254
        ctx:playSound("sounds\\VO\\Charrrge.wav", "DoNothing", 100, 500, "FALSE", 90) -- DP_INTERROGATIONGUARD1.scr:255
    else -- DP_INTERROGATIONGUARD1.scr:256
        ctx:playSound("sounds\\VO\\TheyAreHere.wav", "DoNothing", 100, 500, "FALSE", 90) -- DP_INTERROGATIONGUARD1.scr:257
    end -- DP_INTERROGATIONGUARD1.scr:258
    ctx:self():runTo(ctx:object("hParam"), 25, "BaseInit") -- DP_INTERROGATIONGUARD1.scr:260
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:262
end

script.labels["Main2"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:265
    ctx:state().hDoorMan = ctx:objectOrNil("InterrDoorman") -- DP_INTERROGATIONGUARD1.scr:267
    ctx:state().nVarPath = 0 -- DP_INTERROGATIONGUARD1.scr:268
    ctx:set("nNumMarkers", "nNumMarkers - 2") -- DP_INTERROGATIONGUARD1.scr:269
    ctx:addTrigger("LetsGo", "DoTheWalk") -- DP_INTERROGATIONGUARD1.scr:271
    ctx:addTrigger("Start", "InterrogationRoom") -- DP_INTERROGATIONGUARD1.scr:272
    ctx:addTrigger("NextCell", "Directions") -- DP_INTERROGATIONGUARD1.scr:273
    ctx:onEvent("OnFoundTarget", "CheckPlayer") -- DP_INTERROGATIONGUARD1.scr:274
    ctx:onEvent("OnDamage", "SetKeyValue") -- DP_INTERROGATIONGUARD1.scr:275
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:278
end

script.labels["Main"] = function(ctx)
    -- DP_INTERROGATIONGUARD1.scr:281
    ctx:self():addFriend("PrisonerHumanMaleA") -- DP_INTERROGATIONGUARD1.scr:283
    ctx:getParam(0, "sWayPoint") -- DP_INTERROGATIONGUARD1.scr:284
    ctx:getParam(1, "nNumMarkers") -- DP_INTERROGATIONGUARD1.scr:285
    ctx:getParam(2, "sCellDoorA") -- DP_INTERROGATIONGUARD1.scr:286
    ctx:getParam(3, "sCellDoorB") -- DP_INTERROGATIONGUARD1.scr:287
    ctx:getParam(4, "sCellDoorC") -- DP_INTERROGATIONGUARD1.scr:288
    ctx:getParam(5, "sMyGuard") -- DP_INTERROGATIONGUARD1.scr:289
    ctx:wait(0, .5, "main2") -- DP_INTERROGATIONGUARD1.scr:291
    do return ctx:exit(1) end -- DP_INTERROGATIONGUARD1.scr:293
end

return script
