-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKLEADER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 9, path = "HonkHostility.inc" }

-- HonkLeader.scr
-- by SJR
-- 10-06-01
-- Purpose:script for the
-- leader of ceremony
script.labels["Main"] = function(ctx)
    -- HONKLEADER.scr:28
    ctx:command("getmyhandle", "hFire") -- HONKLEADER.scr:30
    ctx:command("getobjectname", "hFire, sMyName") -- HONKLEADER.scr:31
    ctx:setConsoleStrVar("HONK_PASTOR", "sMyName") -- HONKLEADER.scr:32
    ctx:command("onpoststartworld", "InitHonkFollower") -- HONKLEADER.scr:34
    ctx:command("onpostminisaveload", "InitHonkFollower") -- HONKLEADER.scr:35
    ctx:command("oncachefiles", "CacheFiles") -- HONKLEADER.scr:36
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:38
end

script.labels["CacheFiles"] = function(ctx)
    -- HONKLEADER.scr:41
    ctx:command("cachesound", "\"sounds\\events\\churchbellring.wav\"") -- HONKLEADER.scr:43
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:45
end

script.labels["InitHonkFollower"] = function(ctx)
    -- HONKLEADER.scr:48
    mm9.gosub(script, ctx, "InitStrings") -- HONKLEADER.scr:50
    ctx:addTrigger("FollowerReady", "StartCeremony") -- HONKLEADER.scr:52
    ctx:command("@m", "6 : 15, RingGong, DoNothing") -- HONKLEADER.scr:54
    ctx:command("@m", "6 : 45, EndCeremony, DoNothing") -- HONKLEADER.scr:55
    ctx:command("@m", "18 : 15, RingGong, DoNothing") -- HONKLEADER.scr:57
    ctx:command("@m", "18 : 45, EndCeremony, DoNothing") -- HONKLEADER.scr:58
    mm9.gosub(script, ctx, "InitHonkHostility") -- HONKLEADER.scr:60
    mm9.gosub(script, ctx, "EndCeremony") -- HONKLEADER.scr:61
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:63
end

script.labels["StartCeremony"] = function(ctx)
    -- HONKLEADER.scr:66
    if ctx:condition("bBeginCeremony==TRUE") then -- HONKLEADER.scr:68
        do return ctx:exit("TRUE") end -- HONKLEADER.scr:69
    end -- HONKLEADER.scr:70
    ctx:command("bbeginceremony", "= TRUE") -- HONKLEADER.scr:72
    ctx:command("getobjecthandle", "Brimstone0, hFire") -- HONKLEADER.scr:74
    if ctx:condition("hFire!=0") then -- HONKLEADER.scr:75
        ctx:trigger("hFire", "on") -- HONKLEADER.scr:76
    end -- HONKLEADER.scr:77
    ctx:command("getobjecthandle", "Brimstone1, hFire") -- HONKLEADER.scr:78
    if ctx:condition("hFire!=0") then -- HONKLEADER.scr:79
        ctx:trigger("hFire", "on") -- HONKLEADER.scr:80
    end -- HONKLEADER.scr:81
    ctx:command("facedir", "-1,0,0, 180, RandomPreach") -- HONKLEADER.scr:83
    ctx:command("playsound", "\"sounds\\ambient\\thunder01.wav\", DoNothing, 1, 5000, FALSE, 100") -- HONKLEADER.scr:84
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:86
end

script.labels["RingGong"] = function(ctx)
    -- HONKLEADER.scr:89
    ctx:command("bendceremony", "= FALSE") -- HONKLEADER.scr:91
    ctx:command("bbeginceremony", "= TRUE") -- HONKLEADER.scr:92
    if ctx:condition("bAttended==TRUE") then -- HONKLEADER.scr:93
        do return ctx:exit("TRUE") end -- HONKLEADER.scr:94
    end -- HONKLEADER.scr:95
    ctx:command("battended", "= TRUE") -- HONKLEADER.scr:97
    ctx:command("playsound", "sounds\\events\\churchbellring.wav, DoNothing, 1, 5000, FALSE, 100") -- HONKLEADER.scr:98
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:100
end

script.labels["EndCeremony"] = function(ctx)
    -- HONKLEADER.scr:103
    ctx:command("loopanim", "\"prop-stand\", 0") -- HONKLEADER.scr:105
    ctx:command("stop", "") -- HONKLEADER.scr:106
    ctx:command("bendceremony", "= TRUE") -- HONKLEADER.scr:107
    ctx:command("bbeginceremony", "= FALSE") -- HONKLEADER.scr:108
    ctx:command("getobjecthandle", "Brimstone0, hFire") -- HONKLEADER.scr:110
    if ctx:condition("hFire!=0") then -- HONKLEADER.scr:111
        ctx:trigger("hFire", "Off") -- HONKLEADER.scr:112
    end -- HONKLEADER.scr:113
    ctx:command("getobjecthandle", "Brimstone1, hFire") -- HONKLEADER.scr:115
    if ctx:condition("hFire!=0") then -- HONKLEADER.scr:116
        ctx:trigger("hFire", "Off") -- HONKLEADER.scr:117
    end -- HONKLEADER.scr:118
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:120
end

script.labels["Pace"] = function(ctx)
    -- HONKLEADER.scr:123
    if ctx:condition("bEndCeremony==TRUE") then -- HONKLEADER.scr:125
        do return ctx:exit("TRUE") end -- HONKLEADER.scr:126
    end -- HONKLEADER.scr:127
    ctx:command("getrandomint", "1, 3, nRandom") -- HONKLEADER.scr:129
    ctx:command("arrayget", "spObjects, nRandom, sHolder") -- HONKLEADER.scr:130
    ctx:command("getobjecthandle", "sHolder, hPlatform") -- HONKLEADER.scr:131
    if ctx:condition("hPlatform!=0") then -- HONKLEADER.scr:132
        ctx:command("walkto", "hPlatform, 0, RandomPreach") -- HONKLEADER.scr:133
    end -- HONKLEADER.scr:134
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:136
end

script.labels["RandomPreach"] = function(ctx)
    -- HONKLEADER.scr:139
    ctx:command("stop", "") -- HONKLEADER.scr:141
    ctx:command("facedir", "-1,0,0, 270, DoNothing") -- HONKLEADER.scr:143
    ctx:command("getrandomint", "0, 3, nRandom") -- HONKLEADER.scr:145
    ctx:command("arrayget", "spAnims, nRandom, sHolder") -- HONKLEADER.scr:146
    ctx:command("playanim", "sHolder") -- HONKLEADER.scr:147
    ctx:command("getrandomint", "0, 3, nRandom") -- HONKLEADER.scr:149
    ctx:command("arrayget", "spSounds, nRandom, sHolder") -- HONKLEADER.scr:150
    ctx:command("playsound", "sHolder, Pace, 1, 1000, 0, 100") -- HONKLEADER.scr:151
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:153
end

script.labels["InitStrings"] = function(ctx)
    -- HONKLEADER.scr:156
    ctx:command("arrayput", "spAnims, 0, \"prop-fidget1\"") -- HONKLEADER.scr:158
    ctx:command("arrayput", "spAnims, 1, \"prop-fidget2\"") -- HONKLEADER.scr:159
    ctx:command("arrayput", "spAnims, 2, \"fidget1\"") -- HONKLEADER.scr:160
    ctx:command("arrayput", "spAnims, 3, \"prop-stand\"") -- HONKLEADER.scr:161
    ctx:command("arrayput", "spSounds, 0, \"sounds\\ambient\\thunder04.wav\"") -- HONKLEADER.scr:163
    ctx:command("arrayput", "spSounds, 1, \"sounds\\ambient\\thunder03.wav\"") -- HONKLEADER.scr:164
    ctx:command("arrayput", "spSounds, 2, \"sounds\\ambient\\thunder02.wav\"") -- HONKLEADER.scr:165
    ctx:command("arrayput", "spSounds, 3, \"sounds\\ambient\\thunder01.wav\"") -- HONKLEADER.scr:166
    ctx:command("arrayput", "spObjects, 0, \"PlatformMarker0\"") -- HONKLEADER.scr:168
    ctx:command("arrayput", "spObjects, 1, \"PlatformMarker1\"") -- HONKLEADER.scr:169
    ctx:command("arrayput", "spObjects, 2, \"PlatformMarker2\"") -- HONKLEADER.scr:170
    ctx:command("arrayput", "spObjects, 3, \"PlatformMarker3\"") -- HONKLEADER.scr:171
    do return ctx:exit("TRUE") end -- HONKLEADER.scr:173
end

return script
