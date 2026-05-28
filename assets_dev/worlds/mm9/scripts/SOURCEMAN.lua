-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SOURCEMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 27, path = "BaseGlobals.inc" }

-- SourceMan.scr
-- by SJR
-- 09-21-01
-- Purpose:Used in conjunction with SourceCreature.scr
-- to spawn out of sight and unlock doors
-- when enough have been killed
-- -DEDIT INFO-
-- ScriptParams are:
-- p0 = Number of SpawnMarkers
-- p1 = How many killed before respawn
-- p2 = How many to spawn at a time
-- p3 = String name of creature type
-- p4 = String name of object to trigger when "done"
-- p5 = "Done" after this many
-- Up to 10 spawn markers, named "SpawnMarker[0...9]"
-- Trigger to change spawn location: SetSpawn[0...9] OR SetSpawnRandom OR SetSpawnNext
-- Trigger to force a spawn: ForceSpawn
-- Trigger to shut off completely: Off
-- Trigger to turn back on: On
-- dummy var for Spawn()
-- current spawn index
script.labels["Main"] = function(ctx)
    -- SOURCEMAN.scr:58
    ctx:getParam(0, "NumSpawns") -- SOURCEMAN.scr:60
    ctx:getParam(1, "SpawnCycle") -- SOURCEMAN.scr:61
    ctx:getParam(2, "SpawnSize") -- SOURCEMAN.scr:62
    ctx:getParam(3, "NAME") -- SOURCEMAN.scr:64
    ctx:getParam(4, "sNotifyName") -- SOURCEMAN.scr:65
    ctx:getParam(5, "nQuota") -- SOURCEMAN.scr:66
    ctx:command("wait", "0, .1, InitSourceMan") -- SOURCEMAN.scr:68
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:69
end

script.labels["InitSourceMan"] = function(ctx)
    -- SOURCEMAN.scr:72
    mm9.gosub(script, ctx, "CapParams") -- SOURCEMAN.scr:74
    ctx:command("screaturename", "= NAME + SPACE + KEYWORD + SPACE + SCRIPT") -- SOURCEMAN.scr:75
    ctx:addTrigger("ReSpawn", "OnCreatureDied") -- SOURCEMAN.scr:77
    ctx:addTrigger("ForceSpawn", "OnForceSpawn") -- SOURCEMAN.scr:78
    ctx:addTrigger("Off", "TurnOff") -- SOURCEMAN.scr:79
    ctx:addTrigger("On", "TurnOn") -- SOURCEMAN.scr:80
    ctx:addTrigger("SetSpawnRandom", "ChangeToRandom") -- SOURCEMAN.scr:81
    ctx:addTrigger("SetSpawnNext", "ChangeToNext") -- SOURCEMAN.scr:82
    ctx:addTrigger("SetSpawn0", "ChangeTo0") -- SOURCEMAN.scr:84
    ctx:addTrigger("SetSpawn1", "ChangeTo1") -- SOURCEMAN.scr:85
    ctx:addTrigger("SetSpawn2", "ChangeTo2") -- SOURCEMAN.scr:86
    ctx:addTrigger("SetSpawn3", "ChangeTo3") -- SOURCEMAN.scr:87
    ctx:addTrigger("SetSpawn4", "ChangeTo4") -- SOURCEMAN.scr:88
    ctx:addTrigger("SetSpawn5", "ChangeTo5") -- SOURCEMAN.scr:89
    ctx:addTrigger("SetSpawn6", "ChangeTo6") -- SOURCEMAN.scr:90
    ctx:addTrigger("SetSpawn7", "ChangeTo7") -- SOURCEMAN.scr:91
    ctx:addTrigger("SetSpawn8", "ChangeTo8") -- SOURCEMAN.scr:92
    ctx:addTrigger("SetSpawn9", "ChangeTo9") -- SOURCEMAN.scr:93
    -- these are to do random callbacks
    ctx:command("setcallback", "0, ChangeTo0") -- SOURCEMAN.scr:96
    ctx:command("setcallback", "1, ChangeTo1") -- SOURCEMAN.scr:97
    ctx:command("setcallback", "2, ChangeTo2") -- SOURCEMAN.scr:98
    ctx:command("setcallback", "3, ChangeTo3") -- SOURCEMAN.scr:99
    ctx:command("setcallback", "4, ChangeTo4") -- SOURCEMAN.scr:100
    ctx:command("setcallback", "5, ChangeTo5") -- SOURCEMAN.scr:101
    ctx:command("setcallback", "6, ChangeTo6") -- SOURCEMAN.scr:102
    ctx:command("setcallback", "7, ChangeTo7") -- SOURCEMAN.scr:103
    ctx:command("setcallback", "8, ChangeTo8") -- SOURCEMAN.scr:104
    ctx:command("setcallback", "9, ChangeTo9") -- SOURCEMAN.scr:105
    ctx:command("getobjecthandle", "SpawnMarker0, hSpawnMarker") -- SOURCEMAN.scr:107
    ctx:command("getobjecthandle", "sNotifyName, hDoneObject") -- SOURCEMAN.scr:108
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:110
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:111
end

script.labels["CapParams"] = function(ctx)
    -- SOURCEMAN.scr:114
    if ctx:condition("NumSpawns>10") then -- SOURCEMAN.scr:116
        ctx:command("numspawns", "= 10") -- SOURCEMAN.scr:117
    end -- SOURCEMAN.scr:118
    if ctx:condition("SpawnSize>10") then -- SOURCEMAN.scr:119
        ctx:command("spawnsize", "= 10") -- SOURCEMAN.scr:120
    end -- SOURCEMAN.scr:121
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:122
end

script.labels["OnForceSpawn"] = function(ctx)
    -- SOURCEMAN.scr:125
    if ctx:condition("NumOnScreen>=10") then -- SOURCEMAN.scr:127
        do return ctx:exit("TRUE") end -- SOURCEMAN.scr:128
    end -- SOURCEMAN.scr:129
    ctx:command("numonscreen", "= NumOnScreen + SpawnSize") -- SOURCEMAN.scr:130
    ctx:command("ntemp", "= SpawnSize") -- SOURCEMAN.scr:131
    while ctx:condition("nTemp!=0") do -- SOURCEMAN.scr:132
        ctx:command("spawn", "hCurSpawn, Spawnx,Spawny,Spawnz, sCreatureName") -- SOURCEMAN.scr:133
        ctx:command("ntemp", "= nTemp - 1") -- SOURCEMAN.scr:134
    end -- SOURCEMAN.scr:135
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:136
end

script.labels["OnCreatureDied"] = function(ctx)
    -- SOURCEMAN.scr:139
    if ctx:condition("NumKilled==nQuota") then -- SOURCEMAN.scr:141
        ctx:trigger("hDoneObject", "trigger") -- SOURCEMAN.scr:142
    end -- SOURCEMAN.scr:143
    ctx:command("numkilled", "= NumKilled + 1") -- SOURCEMAN.scr:145
    ctx:command("numonscreen", "= NumOnScreen - 1") -- SOURCEMAN.scr:146
    ctx:command("isnotdivisible", "= NumKilled") -- SOURCEMAN.scr:147
    ctx:command("mod", "IsNotDivisible, SpawnCycle") -- SOURCEMAN.scr:148
    if ctx:condition("IsNotDivisible==0") then -- SOURCEMAN.scr:150
        mm9.gosub(script, ctx, "OnForceSpawn") -- SOURCEMAN.scr:151
    end -- SOURCEMAN.scr:152
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:153
end

script.labels["TurnOn"] = function(ctx)
    -- SOURCEMAN.scr:156
    ctx:addTrigger("ReSpawn", "OnCreatureDied") -- SOURCEMAN.scr:158
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:159
end

script.labels["TurnOff"] = function(ctx)
    -- SOURCEMAN.scr:162
    ctx:command("removetrigger", "ReSpawn") -- SOURCEMAN.scr:164
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:165
end

script.labels["ChangeToRandom"] = function(ctx)
    -- SOURCEMAN.scr:168
    ctx:command("getrandomint", "1, NumSpawns, nTemp") -- SOURCEMAN.scr:170
    if ctx:condition("nTemp==nCurSpawn") then -- SOURCEMAN.scr:171
        ctx:command("ntemp", "= nTemp + 1") -- SOURCEMAN.scr:172
    end -- SOURCEMAN.scr:173
    ctx:command("ncurspawn", "= nTemp") -- SOURCEMAN.scr:174
    ctx:command("docallback", "nCurSpawn") -- SOURCEMAN.scr:175
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:176
end

script.labels["ChangeToNext"] = function(ctx)
    -- SOURCEMAN.scr:179
    ctx:command("ncurspawn", "= nCurSpawn + 1") -- SOURCEMAN.scr:181
    ctx:command("mod", "nCurSpawn, NumSpawns") -- SOURCEMAN.scr:182
    ctx:command("docallback", "nCurSpawn") -- SOURCEMAN.scr:183
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:184
end

script.labels["ChangeTo0"] = function(ctx)
    -- SOURCEMAN.scr:187
    ctx:command("getobjecthandle", "SpawnMarker0, hSpawnMarker") -- SOURCEMAN.scr:189
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:190
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:191
end

script.labels["ChangeTo1"] = function(ctx)
    -- SOURCEMAN.scr:193
    ctx:command("getobjecthandle", "SpawnMarker1, hSpawnMarker") -- SOURCEMAN.scr:195
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:196
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:197
end

script.labels["ChangeTo2"] = function(ctx)
    -- SOURCEMAN.scr:199
    ctx:command("getobjecthandle", "SpawnMarker2, hSpawnMarker") -- SOURCEMAN.scr:201
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:202
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:203
end

script.labels["ChangeTo3"] = function(ctx)
    -- SOURCEMAN.scr:205
    ctx:command("getobjecthandle", "SpawnMarker3, hSpawnMarker") -- SOURCEMAN.scr:207
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:208
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:209
end

script.labels["ChangeTo4"] = function(ctx)
    -- SOURCEMAN.scr:211
    ctx:command("getobjecthandle", "SpawnMarker4, hSpawnMarker") -- SOURCEMAN.scr:213
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:214
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:215
end

script.labels["ChangeTo5"] = function(ctx)
    -- SOURCEMAN.scr:217
    ctx:command("getobjecthandle", "SpawnMarker5, hSpawnMarker") -- SOURCEMAN.scr:219
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:220
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:221
end

script.labels["ChangeTo6"] = function(ctx)
    -- SOURCEMAN.scr:223
    ctx:command("getobjecthandle", "SpawnMarker6, hSpawnMarker") -- SOURCEMAN.scr:225
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:226
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:227
end

script.labels["ChangeTo7"] = function(ctx)
    -- SOURCEMAN.scr:229
    ctx:command("getobjecthandle", "SpawnMarker7, hSpawnMarker") -- SOURCEMAN.scr:231
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:232
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:233
end

script.labels["ChangeTo8"] = function(ctx)
    -- SOURCEMAN.scr:235
    ctx:command("getobjecthandle", "SpawnMarker8, hSpawnMarker") -- SOURCEMAN.scr:237
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:238
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:239
end

script.labels["ChangeTo9"] = function(ctx)
    -- SOURCEMAN.scr:241
    ctx:command("getobjecthandle", "SpawnMarker9, hSpawnMarker") -- SOURCEMAN.scr:243
    ctx:command("getpos", "hSpawnMarker, Spawnx,Spawny,Spawnz") -- SOURCEMAN.scr:244
    do return ctx:exit("TRUE") end -- SOURCEMAN.scr:245
end

return script
