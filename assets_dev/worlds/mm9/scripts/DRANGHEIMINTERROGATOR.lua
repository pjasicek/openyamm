-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRANGHEIMINTERROGATOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "ListTraverse.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "DrangheimHostility.inc" }

-- DrangheimInterrogator.scr
-- by SJR
-- Purpose:
-- hardcode these later
script.labels["Main"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:37
    ctx:getParam(0, "LISTNAME") -- DRANGHEIMINTERROGATOR.scr:39
    ctx:getParam(1, "LISTFIRST") -- DRANGHEIMINTERROGATOR.scr:40
    ctx:getParam(2, "LISTLAST") -- DRANGHEIMINTERROGATOR.scr:41
    ctx:command("onpoststartworld", "InitDrangheimInterrogator") -- DRANGHEIMINTERROGATOR.scr:43
    ctx:command("onpostminisaveload", "InitDrangheimInterrogator") -- DRANGHEIMINTERROGATOR.scr:44
    ctx:command("oncachefiles", "CacheFiles") -- DRANGHEIMINTERROGATOR.scr:45
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:47
end

script.labels["CacheFiles"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:50
    ctx:command("cachesound", "\"sounds\\events\\BeatdownMix8bit.wav\"") -- DRANGHEIMINTERROGATOR.scr:52
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:54
end

script.labels["InitDrangheimInterrogator"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:57
    -- setup hostility and triggers
    ctx:command("getmyhandle", "hMe") -- DRANGHEIMINTERROGATOR.scr:60
    ctx:command("getstat", "hMe, WalkVel, nMyWalk") -- DRANGHEIMINTERROGATOR.scr:61
    ctx:command("getobjecthandle", "InterrWarden, hWarden") -- DRANGHEIMINTERROGATOR.scr:62
    ctx:command("getobjecthandle", "InterrDoorman, hDoorman") -- DRANGHEIMINTERROGATOR.scr:63
    ctx:command("getobjecthandle", "CellDoor13, hDummy") -- DRANGHEIMINTERROGATOR.scr:64
    if ctx:condition("hDummy!=0") then -- DRANGHEIMINTERROGATOR.scr:65
        ctx:command("getstat", "hDummy, DoorOpenTime, CELL_OPEN_TIME") -- DRANGHEIMINTERROGATOR.scr:66
    end -- DRANGHEIMINTERROGATOR.scr:67
    ctx:command("getobjecthandle", "RightDoor0, hDummy") -- DRANGHEIMINTERROGATOR.scr:68
    if ctx:condition("hDummy!=0") then -- DRANGHEIMINTERROGATOR.scr:69
        ctx:command("getstat", "hDummy, DoorOpenTime, DOOR_OPEN_TIME") -- DRANGHEIMINTERROGATOR.scr:70
    end -- DRANGHEIMINTERROGATOR.scr:71
    if ctx:condition("hWarden!=0") then -- DRANGHEIMINTERROGATOR.scr:73
        ctx:command("createobjectlink", "hWarden") -- DRANGHEIMINTERROGATOR.scr:74
    end -- DRANGHEIMINTERROGATOR.scr:75
    if ctx:condition("hDoorman!=0") then -- DRANGHEIMINTERROGATOR.scr:76
        ctx:command("createobjectlink", "hDoorman") -- DRANGHEIMINTERROGATOR.scr:77
    end -- DRANGHEIMINTERROGATOR.scr:78
    ctx:command("onobjectlinkbroken", "OnObjectLinkBroken") -- DRANGHEIMINTERROGATOR.scr:79
    -- add a little grace period
    ctx:command("door_open_time", "= DOOR_OPEN_TIME + 1") -- DRANGHEIMINTERROGATOR.scr:82
    ctx:command("cell_open_time", "= CELL_OPEN_TIME + 1") -- DRANGHEIMINTERROGATOR.scr:83
    mm9.gosub(script, ctx, "InitDrangheimHostility") -- DRANGHEIMINTERROGATOR.scr:85
    mm9.gosub(script, ctx, "SetTraverseWalk") -- DRANGHEIMINTERROGATOR.scr:87
    mm9.gosub(script, ctx, "SetTraversePace") -- DRANGHEIMINTERROGATOR.scr:88
    ctx:command("traverseradius", "= 5") -- DRANGHEIMINTERROGATOR.scr:89
    ctx:command("onstuck", "TraverseResume") -- DRANGHEIMINTERROGATOR.scr:91
    ctx:addTrigger("start", "StartScript") -- DRANGHEIMINTERROGATOR.scr:93
    ctx:addTrigger("outside", "OnPrisonerOut") -- DRANGHEIMINTERROGATOR.scr:94
    ctx:addTrigger("inside", "OnPrisonerIn") -- DRANGHEIMINTERROGATOR.scr:95
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:97
end

script.labels["OnObjectLinkBroken"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:100
    ctx:getParam(0, "hLinkBroken") -- DRANGHEIMINTERROGATOR.scr:102
    if ctx:condition("hLinkBroken==hWarden") then -- DRANGHEIMINTERROGATOR.scr:103
        ctx:command("hwarden", "= NULL") -- DRANGHEIMINTERROGATOR.scr:104
    else -- DRANGHEIMINTERROGATOR.scr:105
        if ctx:condition("hLinkBroken==hDoorman") then -- DRANGHEIMINTERROGATOR.scr:106
            ctx:command("hdoorman", "= NULL") -- DRANGHEIMINTERROGATOR.scr:107
        end -- DRANGHEIMINTERROGATOR.scr:108
    end -- DRANGHEIMINTERROGATOR.scr:109
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:111
end

script.labels["StartScript"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:114
    -- get all the handles, start moving
    ctx:command("removetrigger", "start") -- DRANGHEIMINTERROGATOR.scr:117
    ctx:command("ncounter", "= 0") -- DRANGHEIMINTERROGATOR.scr:119
    ctx:command("breturning", "= FALSE") -- DRANGHEIMINTERROGATOR.scr:120
    ctx:command("listindex", "= LISTFIRST") -- DRANGHEIMINTERROGATOR.scr:121
    mm9.gosub(script, ctx, "TraverseBegin") -- DRANGHEIMINTERROGATOR.scr:122
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:124
end

script.labels["GetNextPrisoner"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:127
    -- change cells, signal to open
    if ctx:condition("hWarden!=0") then -- DRANGHEIMINTERROGATOR.scr:130
        ctx:trigger("hWarden", "change") -- DRANGHEIMINTERROGATOR.scr:131
        ctx:trigger("hWarden", "open") -- DRANGHEIMINTERROGATOR.scr:132
    end -- DRANGHEIMINTERROGATOR.scr:133
    ctx:command("wait", "0, CELL_OPEN_TIME, EscortNextPrisoner") -- DRANGHEIMINTERROGATOR.scr:135
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:137
end

script.labels["EscortNextPrisoner"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:140
    -- get prisoner, addfriend, signal exit
    ctx:command("sprisonername", "= PRISONER_BASE + nCounter") -- DRANGHEIMINTERROGATOR.scr:143
    ctx:command("getobjecthandle", "sPrisonerName, hPrisoner") -- DRANGHEIMINTERROGATOR.scr:144
    if ctx:condition("hPrisoner!=0") then -- DRANGHEIMINTERROGATOR.scr:146
        ctx:command("getclassname", "hPrisoner, sTemp") -- DRANGHEIMINTERROGATOR.scr:147
        ctx:command("addfriend", "sTemp") -- DRANGHEIMINTERROGATOR.scr:148
        ctx:command("getstat", "hPrisoner, WalkVel, nTemp") -- DRANGHEIMINTERROGATOR.scr:149
        ctx:command("setstat", "hMe, WalkVel, nTemp") -- DRANGHEIMINTERROGATOR.scr:150
        ctx:command("playanim", "ANIM_COMEOUT, OnSignalComeOut") -- DRANGHEIMINTERROGATOR.scr:151
    end -- DRANGHEIMINTERROGATOR.scr:152
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:154
end

script.labels["OnSignalComeOut"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:157
    -- tell prisoner to leave cell
    if ctx:condition("hPrisoner!=0") then -- DRANGHEIMINTERROGATOR.scr:160
        ctx:trigger("hPrisoner", "leave") -- DRANGHEIMINTERROGATOR.scr:161
    end -- DRANGHEIMINTERROGATOR.scr:162
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:164
end

script.labels["OnPrisonerOut"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:167
    -- signal to shut cell
    ctx:command("playanim", "ANIM_SHUTCELL, OnSignalShutCell") -- DRANGHEIMINTERROGATOR.scr:170
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:172
end

script.labels["OnSignalShutCell"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:175
    -- take prisoner to interrogation room
    if ctx:condition("hPrisoner!=0") then -- DRANGHEIMINTERROGATOR.scr:178
        ctx:trigger("hPrisoner", "followme") -- DRANGHEIMINTERROGATOR.scr:179
    end -- DRANGHEIMINTERROGATOR.scr:180
    if ctx:condition("hWarden!=0") then -- DRANGHEIMINTERROGATOR.scr:181
        ctx:trigger("hWarden", "close") -- DRANGHEIMINTERROGATOR.scr:182
    end -- DRANGHEIMINTERROGATOR.scr:183
    ctx:command("wait", "0, CELL_OPEN_TIME, TraverseResume") -- DRANGHEIMINTERROGATOR.scr:185
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:187
end

script.labels["OnPrisonerIn"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:190
    -- close cell, go to next prisoner
    if ctx:condition("hWarden!=0") then -- DRANGHEIMINTERROGATOR.scr:193
        ctx:trigger("hWarden", "close") -- DRANGHEIMINTERROGATOR.scr:194
    end -- DRANGHEIMINTERROGATOR.scr:195
    if ctx:condition("nCounter==3") then -- DRANGHEIMINTERROGATOR.scr:197
        ctx:addTrigger("start", "StartScript") -- DRANGHEIMINTERROGATOR.scr:198
        ctx:command("ncounter", "= 0") -- DRANGHEIMINTERROGATOR.scr:199
        ctx:command("setstat", "hMe, WalkVel, nMyWalk") -- DRANGHEIMINTERROGATOR.scr:200
        do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:201
    else -- DRANGHEIMINTERROGATOR.scr:202
        mm9.gosub(script, ctx, "TraverseResume") -- DRANGHEIMINTERROGATOR.scr:203
    end -- DRANGHEIMINTERROGATOR.scr:204
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:206
end

script.labels["OnBeatingStart"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:209
    -- play beating sound, callback
    mm9.gosub(script, ctx, "TraversePause") -- DRANGHEIMINTERROGATOR.scr:212
    ctx:command("playsound", "\"sounds\\events\\BeatdownMix8bit.wav\", OnBeatingDone, 1, 500, FALSE, 100") -- DRANGHEIMINTERROGATOR.scr:213
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:215
end

script.labels["OnBeatingDone"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:218
    -- open door, take prisoner back to cell
    if ctx:condition("hDoorman!=0") then -- DRANGHEIMINTERROGATOR.scr:221
        ctx:trigger("hDoorman", "open") -- DRANGHEIMINTERROGATOR.scr:222
    end -- DRANGHEIMINTERROGATOR.scr:223
    ctx:command("breturning", "= TRUE") -- DRANGHEIMINTERROGATOR.scr:224
    ctx:command("wait", "0, DOOR_OPEN_TIME, TraverseResume") -- DRANGHEIMINTERROGATOR.scr:225
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:227
end

script.labels["OnReturned"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:230
    -- signal prisoner to return to cell
    ctx:command("playanim", "ANIM_GOBACK, OnSignalGoBack") -- DRANGHEIMINTERROGATOR.scr:233
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:235
end

script.labels["OnSignalGoBack"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:238
    -- trigger return to cell
    if ctx:condition("hPrisoner!=0") then -- DRANGHEIMINTERROGATOR.scr:241
        ctx:trigger("hPrisoner", "return") -- DRANGHEIMINTERROGATOR.scr:242
    end -- DRANGHEIMINTERROGATOR.scr:243
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:245
end

script.labels["OnTraverseDone"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:248
    -- check where we are, do stuff accordingly
    if ctx:condition("LISTINDEX==8") then -- DRANGHEIMINTERROGATOR.scr:251
        mm9.gosub(script, ctx, "TraversePause") -- DRANGHEIMINTERROGATOR.scr:252
        if ctx:condition("hDoorman!=0") then -- DRANGHEIMINTERROGATOR.scr:253
            if ctx:condition("bReturning==TRUE") then -- DRANGHEIMINTERROGATOR.scr:254
                ctx:trigger("hDoorman", "close") -- DRANGHEIMINTERROGATOR.scr:255
            else -- DRANGHEIMINTERROGATOR.scr:256
                ctx:trigger("hDoorman", "open") -- DRANGHEIMINTERROGATOR.scr:257
            end -- DRANGHEIMINTERROGATOR.scr:258
            ctx:command("wait", "0, DOOR_OPEN_TIME, TraverseResume") -- DRANGHEIMINTERROGATOR.scr:260
        end -- DRANGHEIMINTERROGATOR.scr:261
    else -- DRANGHEIMINTERROGATOR.scr:262
        if ctx:condition("LISTINDEX==9") then -- DRANGHEIMINTERROGATOR.scr:264
            if ctx:condition("bReturning==FALSE") then -- DRANGHEIMINTERROGATOR.scr:265
                mm9.gosub(script, ctx, "TraversePause") -- DRANGHEIMINTERROGATOR.scr:266
                if ctx:condition("hDoorman!=0") then -- DRANGHEIMINTERROGATOR.scr:267
                    ctx:trigger("hDoorman", "close") -- DRANGHEIMINTERROGATOR.scr:268
                    ctx:command("wait", "0, DOOR_OPEN_TIME, OnBeatingStart") -- DRANGHEIMINTERROGATOR.scr:269
                end -- DRANGHEIMINTERROGATOR.scr:270
            end -- DRANGHEIMINTERROGATOR.scr:271
        else -- DRANGHEIMINTERROGATOR.scr:272
            if ctx:condition("LISTINDEX==nCounter") then -- DRANGHEIMINTERROGATOR.scr:274
                mm9.gosub(script, ctx, "TraversePause") -- DRANGHEIMINTERROGATOR.scr:275
                if ctx:condition("bReturning==TRUE") then -- DRANGHEIMINTERROGATOR.scr:276
                    if ctx:condition("hWarden!=0") then -- DRANGHEIMINTERROGATOR.scr:277
                        ctx:command("ncounter", "= nCounter + 1") -- DRANGHEIMINTERROGATOR.scr:278
                        ctx:trigger("hWarden", "open") -- DRANGHEIMINTERROGATOR.scr:279
                        ctx:command("wait", "0, CELL_OPEN_TIME, OnReturned") -- DRANGHEIMINTERROGATOR.scr:280
                        ctx:command("breturning", "= FALSE") -- DRANGHEIMINTERROGATOR.scr:281
                    end -- DRANGHEIMINTERROGATOR.scr:282
                else -- DRANGHEIMINTERROGATOR.scr:283
                    mm9.gosub(script, ctx, "GetNextPrisoner") -- DRANGHEIMINTERROGATOR.scr:284
                end -- DRANGHEIMINTERROGATOR.scr:285
            else -- DRANGHEIMINTERROGATOR.scr:286
                if ctx:condition("LISTINDEX==LISTFIRST") then -- DRANGHEIMINTERROGATOR.scr:288
                    mm9.gosub(script, ctx, "TraversePause") -- DRANGHEIMINTERROGATOR.scr:289
                    if ctx:condition("hWarden!=0") then -- DRANGHEIMINTERROGATOR.scr:290
                        ctx:command("faceobject", "hWarden, 180, OnSignalOpenCell") -- DRANGHEIMINTERROGATOR.scr:291
                    end -- DRANGHEIMINTERROGATOR.scr:292
                end -- DRANGHEIMINTERROGATOR.scr:293
            end -- DRANGHEIMINTERROGATOR.scr:294
        end -- DRANGHEIMINTERROGATOR.scr:295
    end -- DRANGHEIMINTERROGATOR.scr:296
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:298
end

script.labels["OnSignalOpenCell"] = function(ctx)
    -- DRANGHEIMINTERROGATOR.scr:301
    -- wait til cell is open, get prisoner
    ctx:command("playanim", "ANIM_OPENCELL, TraverseResume") -- DRANGHEIMINTERROGATOR.scr:304
    do return ctx:exit("TRUE") end -- DRANGHEIMINTERROGATOR.scr:306
end

return script
