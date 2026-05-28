-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BATTLEMAN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- BattleMan.scr
-- timmy
-- handles the Battle of Frosgard stuff
script.labels["Spawn"] = function(ctx)
    -- BATTLEMAN.scr:33
    ctx:giveKey(377) -- BATTLEMAN.scr:36
    ctx:command("getobjecthandle", "ForadDarre g_hobject") -- BATTLEMAN.scr:38
    ctx:trigger("g_hobject", "Appear") -- BATTLEMAN.scr:39
    ctx:command("getobjecthandle", "TamurLeng0 g_hobject") -- BATTLEMAN.scr:41
    ctx:trigger("g_hobject", "Appear") -- BATTLEMAN.scr:42
    ctx:command("set", "SCRIPT \" ScriptName HateNPC.scr\"") -- BATTLEMAN.scr:44
    -- screenfadeout 1
    ctx:command("wait", "1 1 FadeIn") -- BATTLEMAN.scr:46
    ctx:command("smonstera", "= sMonsterA + Script") -- BATTLEMAN.scr:48
    ctx:command("smonsterb", "= sMonsterB + Script") -- BATTLEMAN.scr:49
    ctx:command("smonsterc", "= sMonsterC + Script") -- BATTLEMAN.scr:50
    ctx:command("getobjecthandle", "Atlimarker g_hobject") -- BATTLEMAN.scr:53
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- BATTLEMAN.scr:54
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:55
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:56
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- BATTLEMAN.scr:57
    ctx:command("spawn", "hMonsterC Xpos YPos ZPos sMonsterC") -- BATTLEMAN.scr:58
    ctx:command("getobjecthandle", "BadGuys0 g_hobject") -- BATTLEMAN.scr:60
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- BATTLEMAN.scr:61
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:62
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:63
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- BATTLEMAN.scr:64
    ctx:command("getobjecthandle", "BadGuys2 g_hobject") -- BATTLEMAN.scr:66
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- BATTLEMAN.scr:67
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:68
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:69
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- BATTLEMAN.scr:70
    ctx:command("getobjecthandle", "BadGuys3 g_hobject") -- BATTLEMAN.scr:72
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- BATTLEMAN.scr:73
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- BATTLEMAN.scr:74
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterC") -- BATTLEMAN.scr:75
    do return ctx:exit("") end -- BATTLEMAN.scr:77
end

script.labels["FadeIn"] = function(ctx)
    -- BATTLEMAN.scr:82
    -- letterbox true
    -- getobjecthandle Camera3 g_hobject
    -- trigger g_hobject On
    -- screenfadein 1
    ctx:command("wait", "1 5 GoodGuys") -- BATTLEMAN.scr:89
    do return ctx:exit("") end -- BATTLEMAN.scr:90
end

script.labels["GoodGuys"] = function(ctx)
    -- BATTLEMAN.scr:93
    ctx:command("set", "SCRIPT \" ScriptName Hate.scr\"") -- BATTLEMAN.scr:96
    ctx:command("sgoodguya", "= sGoodGuyA + Script") -- BATTLEMAN.scr:98
    ctx:command("sgoodguyb", "= sGoodGuyB + Script") -- BATTLEMAN.scr:99
    ctx:command("sgoodguyc", "= sGoodGuyc + Script") -- BATTLEMAN.scr:100
    ctx:command("getobjecthandle", "GoodGuys g_hobject") -- BATTLEMAN.scr:104
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- BATTLEMAN.scr:105
    -- Spawn hMonsterC Xpos YPos ZPos sKira
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sGoodGuyA") -- BATTLEMAN.scr:108
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sGoodGuyB") -- BATTLEMAN.scr:109
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sGoodGuyB") -- BATTLEMAN.scr:110
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sGoodGuyC") -- BATTLEMAN.scr:111
    ctx:command("wait", "1 5 End") -- BATTLEMAN.scr:113
    do return ctx:exit("") end -- BATTLEMAN.scr:114
end

script.labels["End"] = function(ctx)
    -- BATTLEMAN.scr:117
    ctx:command("getobjecthandle", "BadGuys0 g_hobject") -- BATTLEMAN.scr:120
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- BATTLEMAN.scr:121
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:122
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:123
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- BATTLEMAN.scr:124
    -- screenfadeout 1
    -- wait 1 1 FadeIn2
    do return ctx:exit("") end -- BATTLEMAN.scr:128
end

script.labels["FadeIn2"] = function(ctx)
    -- BATTLEMAN.scr:131
end

-- letterbox false
-- getobjecthandle Camera3 g_hobject
-- trigger g_hobject Off
-- screenfadein 1
-- exit
script.labels["OnFight2"] = function(ctx)
    -- BATTLEMAN.scr:141
    if not ctx:hasKey(104) then -- BATTLEMAN.scr:144-145
        do return ctx:exit("") end -- BATTLEMAN.scr:146
    end -- BATTLEMAN.scr:147
    ctx:command("getobjecthandle", "BadGuys1 g_hobject") -- BATTLEMAN.scr:150
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- BATTLEMAN.scr:151
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:152
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sMonsterA") -- BATTLEMAN.scr:153
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterB") -- BATTLEMAN.scr:154
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sMonsterC") -- BATTLEMAN.scr:155
    ctx:command("getobjecthandle", "GoodGuys0 g_hobject") -- BATTLEMAN.scr:160
    ctx:command("getpos", "g_hobject XPos YPos ZPos") -- BATTLEMAN.scr:161
    ctx:command("spawn", "hMonsterA Xpos YPos ZPos sGoodGuyA") -- BATTLEMAN.scr:164
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sGoodGuyB") -- BATTLEMAN.scr:165
    ctx:command("spawn", "hMonsterB Xpos YPos ZPos sGoodGuyB") -- BATTLEMAN.scr:166
    do return ctx:exit("") end -- BATTLEMAN.scr:168
end

script.labels["Init"] = function(ctx)
    -- BATTLEMAN.scr:171
    if ctx:hasKey(377) then -- BATTLEMAN.scr:174-175
        do return ctx:exit("") end -- BATTLEMAN.scr:176
    end -- BATTLEMAN.scr:177
    if ctx:hasKey(104) then -- BATTLEMAN.scr:179-180
        mm9.gosub(script, ctx, "spawn") -- BATTLEMAN.scr:181
        do return ctx:exit("") end -- BATTLEMAN.scr:182
    end -- BATTLEMAN.scr:183
    do return ctx:exit("") end -- BATTLEMAN.scr:185
end

script.labels["Main"] = function(ctx)
    -- BATTLEMAN.scr:189
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Fight2", "OnFight2") -- BATTLEMAN.scr:194
    ctx:command("onpoststartworld", "Init") -- BATTLEMAN.scr:195
    ctx:command("onpostminisaveload", "Init") -- BATTLEMAN.scr:196
    ctx:command("onpostsaveload", "Init") -- BATTLEMAN.scr:197
    ctx:command("wait", "1 .1 Init") -- BATTLEMAN.scr:198
    do return ctx:exit("") end -- BATTLEMAN.scr:199
end

return script
