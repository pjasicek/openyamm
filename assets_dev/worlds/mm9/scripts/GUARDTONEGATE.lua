-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "GUARDTONEGATE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "BaseMelee.inc" }

-- GuardToNegate.scr
-- Karl
-- 10-17-01
-- Guards move to Marker in hallway
-- to attack the Nagates
-- P0 = Guard that other Guards face
-- P1 = Starting Position Marker
script.labels["WalkBack"] = function(ctx)
    -- GUARDTONEGATE.scr:34
    ctx:command("hguardmarker", "= NULL") -- GUARDTONEGATE.scr:37
    ctx:command("getobjecthandle", "sStartingPos, hGuardMarker") -- GUARDTONEGATE.scr:38
    ctx:command("walkto", "hGuardMarker, 0, DoNothing") -- GUARDTONEGATE.scr:39
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:40
end

script.labels["BackToStart"] = function(ctx)
    -- GUARDTONEGATE.scr:43
    mm9.gosub(script, ctx, "ontargetdead") -- GUARDTONEGATE.scr:45
    ctx:command("wait", "0 2 WalkBack") -- GUARDTONEGATE.scr:46
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:47
end

script.labels["WereHere2"] = function(ctx)
    -- GUARDTONEGATE.scr:49
    ctx:command("stop", "") -- GUARDTONEGATE.scr:51
    ctx:command("wait", "0, 2, DoNothing") -- GUARDTONEGATE.scr:52
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:53
end

script.labels["NagateMarker"] = function(ctx)
    -- GUARDTONEGATE.scr:55
    ctx:command("hguardmarker", "= NULL") -- GUARDTONEGATE.scr:57
    ctx:command("getobjecthandle", "NagateMarker3, hGuardMarker") -- GUARDTONEGATE.scr:58
    ctx:command("runto", "hGuardMarker, 0, DoNothing") -- GUARDTONEGATE.scr:59
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:60
end

script.labels["FaceEachOther"] = function(ctx)
    -- GUARDTONEGATE.scr:62
    if ctx:condition("sWhoAmI==BarracksGuard2") then -- GUARDTONEGATE.scr:64
        ctx:command("playsound", "sounds\\VO\\IRequireAssistance.WAV, DoNothing, hDummy, 5000, FALSE, 100") -- GUARDTONEGATE.scr:65
    end -- GUARDTONEGATE.scr:66
    ctx:command("faceobject", "hGuard, 180, NagateMarker") -- GUARDTONEGATE.scr:67
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:68
end

script.labels["WereHere"] = function(ctx)
    -- GUARDTONEGATE.scr:70
    ctx:command("stop", "") -- GUARDTONEGATE.scr:72
    ctx:command("wait", "0, 2, FaceEachOther") -- GUARDTONEGATE.scr:73
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:74
end

script.labels["PlayerIsHere"] = function(ctx)
    -- GUARDTONEGATE.scr:76
    ctx:command("getobjecthandle", "NagateMarker2, hGuardMarker") -- GUARDTONEGATE.scr:78
    ctx:command("runto", "hGuardMarker, 2, WereHere") -- GUARDTONEGATE.scr:79
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:80
end

script.labels["CheckPlayer"] = function(ctx)
    -- GUARDTONEGATE.scr:82
    ctx:getParam(0, "hParam") -- GUARDTONEGATE.scr:84
    ctx:command("isplayer", "hParam, bIsPlayer") -- GUARDTONEGATE.scr:85
    if ctx:condition("bIsPlayer==TRUE") then -- GUARDTONEGATE.scr:87
        ctx:hasKey(5007, "bHasFriendlyKey") -- GUARDTONEGATE.scr:88
        ctx:hasKey(5006, "bHasHostileKey") -- GUARDTONEGATE.scr:89
        ctx:command("bhashostilekey", "= 1 - bHasHostileKey") -- GUARDTONEGATE.scr:90
        ctx:command("bresult", "= bHasFriendlyKey * bHasHostileKey * bIsPlayer") -- GUARDTONEGATE.scr:91
        if ctx:condition("bResult == FALSE") then -- GUARDTONEGATE.scr:92
            ctx:giveKey(5006) -- GUARDTONEGATE.scr:93
            mm9.gosub(script, ctx, "AlertCall") -- GUARDTONEGATE.scr:94
        else -- GUARDTONEGATE.scr:95
            ctx:command("addfriend", "Player") -- GUARDTONEGATE.scr:96
        end -- GUARDTONEGATE.scr:97
    else -- GUARDTONEGATE.scr:98
        mm9.gosub(script, ctx, "baseinit") -- GUARDTONEGATE.scr:99
        ctx:command("ontargetdead", "BackToStart") -- GUARDTONEGATE.scr:100
    end -- GUARDTONEGATE.scr:102
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:104
end

script.labels["SetKeyValue"] = function(ctx)
    -- GUARDTONEGATE.scr:106
    ctx:getParam(0, "hParam") -- GUARDTONEGATE.scr:108
    ctx:command("isplayer", "hParam, bIsPlayer") -- GUARDTONEGATE.scr:109
    if ctx:condition("bIsPlayer==TRUE") then -- GUARDTONEGATE.scr:110
        ctx:giveKey(5006) -- GUARDTONEGATE.scr:111
        ctx:command("removefriend", "Player") -- GUARDTONEGATE.scr:112
        mm9.gosub(script, ctx, "AlertCall") -- GUARDTONEGATE.scr:113
    else -- GUARDTONEGATE.scr:114
        ctx:command("addfriend", "Player") -- GUARDTONEGATE.scr:115
        mm9.gosub(script, ctx, "baseinit") -- GUARDTONEGATE.scr:116
        ctx:command("ontargetdead", "BackToStart") -- GUARDTONEGATE.scr:117
    end -- GUARDTONEGATE.scr:118
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:119
end

script.labels["AlertCall"] = function(ctx)
    -- GUARDTONEGATE.scr:121
    if ctx:condition("sWhoAmI!=BarracksGuard2") then -- GUARDTONEGATE.scr:123
        ctx:command("playsound", "sounds\\VO\\Charrrge.wav, DoNothing, hDummy, 5000, FALSE, 100") -- GUARDTONEGATE.scr:124
    else -- GUARDTONEGATE.scr:125
        ctx:command("playsound", "sounds\\VO\\TheyAreHere.wav, DoNothing, hDummy, 5000, FALSE, 100") -- GUARDTONEGATE.scr:126
    end -- GUARDTONEGATE.scr:127
    ctx:command("runto", "hParam, 25, BaseInit") -- GUARDTONEGATE.scr:128
    do return ctx:exit("TRUE") end -- GUARDTONEGATE.scr:129
end

script.labels["Main2"] = function(ctx)
    -- GUARDTONEGATE.scr:131
    ctx:addTrigger("Hello", "PlayerIsHere") -- GUARDTONEGATE.scr:133
    ctx:command("addenemy", "Nagate") -- GUARDTONEGATE.scr:134
    ctx:command("addfriend", "PrisonerHumanMaleA") -- GUARDTONEGATE.scr:135
    ctx:command("onfoundtarget", "CheckPlayer") -- GUARDTONEGATE.scr:136
    ctx:command("ondamage", "SetKeyValue") -- GUARDTONEGATE.scr:137
    ctx:command("ontargetdead", "BackToStart") -- GUARDTONEGATE.scr:138
    ctx:command("getobjecthandle", "sGuard, hGuard") -- GUARDTONEGATE.scr:139
    ctx:command("getobjecthandle", "sStartingPos, hGuardStart") -- GUARDTONEGATE.scr:140
    do return ctx:exit("") end -- GUARDTONEGATE.scr:142
end

script.labels["Main"] = function(ctx)
    -- GUARDTONEGATE.scr:144
    ctx:getParam(0, "sGuard") -- GUARDTONEGATE.scr:146
    ctx:getParam(1, "sStartingPos") -- GUARDTONEGATE.scr:147
    ctx:getParam(2, "sWhoAmI") -- GUARDTONEGATE.scr:148
    ctx:command("cachesound", "sounds\\VO\\IRequireAssistance.WAV") -- GUARDTONEGATE.scr:149
    ctx:command("cachesound", "sounds\\VO\\TheyAreHere.wav") -- GUARDTONEGATE.scr:150
    ctx:command("cachesound", "sounds\\VO\\Charrrge.wav") -- GUARDTONEGATE.scr:151
    ctx:command("wait", "1, 0.5, Main2") -- GUARDTONEGATE.scr:154
    do return ctx:exit("") end -- GUARDTONEGATE.scr:155
end

return script
