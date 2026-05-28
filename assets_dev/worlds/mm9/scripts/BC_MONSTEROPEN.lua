-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BC_MONSTEROPEN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }

-- BC_MonsterFight.scr
-- by SJR
-- Purpose:two monsters duke it out
-- to show the player a fight
script.labels["Main"] = function(ctx)
    -- BC_MONSTEROPEN.scr:14
    ctx:command("wait", "0, .1, InitMonsterOpen") -- BC_MONSTEROPEN.scr:16
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:18
end

script.labels["InitMonsterOpen"] = function(ctx)
    -- BC_MONSTEROPEN.scr:21
    ctx:command("addfriend", "AIBase") -- BC_MONSTEROPEN.scr:23
    ctx:command("addfriend", "Player") -- BC_MONSTEROPEN.scr:24
    ctx:command("getobjecthandle", "TreasureChest0, hTreasure2") -- BC_MONSTEROPEN.scr:26
    ctx:command("getobjecthandle", "TreasureChest3, hTreasure1") -- BC_MONSTEROPEN.scr:27
    ctx:command("getobjecthandle", "TreasureChest4, hTreasure0") -- BC_MONSTEROPEN.scr:28
    ctx:command("wait", "0, 1, BeginOpen") -- BC_MONSTEROPEN.scr:30
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:32
end

script.labels["BeginOpen"] = function(ctx)
    -- BC_MONSTEROPEN.scr:35
    mm9.gosub(script, ctx, "WalkToFirst") -- BC_MONSTEROPEN.scr:37
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:39
end

script.labels["DieHard"] = function(ctx)
    -- BC_MONSTEROPEN.scr:42
    ctx:command("die", "") -- BC_MONSTEROPEN.scr:44
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:46
end

script.labels["WalkToFirst"] = function(ctx)
    -- BC_MONSTEROPEN.scr:49
    ctx:command("walkto", "hTreasure0, 0, OpenFirst") -- BC_MONSTEROPEN.scr:51
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:53
end

script.labels["WalkToSecond"] = function(ctx)
    -- BC_MONSTEROPEN.scr:56
    ctx:command("walkto", "hTreasure1, 0, OpenSecond") -- BC_MONSTEROPEN.scr:58
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:60
end

script.labels["WalkToThird"] = function(ctx)
    -- BC_MONSTEROPEN.scr:63
    ctx:command("walkto", "hTreasure2, 0, OpenThird") -- BC_MONSTEROPEN.scr:65
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:67
end

script.labels["OpenFirst"] = function(ctx)
    -- BC_MONSTEROPEN.scr:70
    ctx:command("stop", "") -- BC_MONSTEROPEN.scr:72
    ctx:command("faceobject", "hTreasure0, 180, DoNothing") -- BC_MONSTEROPEN.scr:73
    ctx:trigger("hTreasure0", "open") -- BC_MONSTEROPEN.scr:75
    ctx:command("playanim", "castspell3, DoNothing") -- BC_MONSTEROPEN.scr:77
    ctx:command("playsound", "\"sounds\\ambient\\people\\crowdnoise-cheer01.wav\", WalkToSecond, 1, 1000, FALSE, 100") -- BC_MONSTEROPEN.scr:78
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:80
end

script.labels["OpenSecond"] = function(ctx)
    -- BC_MONSTEROPEN.scr:83
    ctx:command("stop", "") -- BC_MONSTEROPEN.scr:85
    ctx:command("faceobject", "hTreasure1, 180, DoNothing") -- BC_MONSTEROPEN.scr:86
    ctx:trigger("hTreasure1", "open") -- BC_MONSTEROPEN.scr:88
    ctx:command("playanim", "castspell3, DoNothing") -- BC_MONSTEROPEN.scr:90
    ctx:command("playsound", "\"sounds\\ambient\\people\\crowdnoise-cheer02.wav\", WalkToThird, 1, 1000, FALSE, 100") -- BC_MONSTEROPEN.scr:91
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:93
end

script.labels["OpenThird"] = function(ctx)
    -- BC_MONSTEROPEN.scr:97
    ctx:command("stop", "") -- BC_MONSTEROPEN.scr:99
    ctx:command("faceobject", "hTreasure2, 180, DoNothing") -- BC_MONSTEROPEN.scr:100
    ctx:trigger("hTreasure2", "open") -- BC_MONSTEROPEN.scr:102
    ctx:command("playsound", "WHY_DO_PEOPLE_USE_SPACES, DoNothing, 1, 1000, FALSE, 100") -- BC_MONSTEROPEN.scr:104
    do return ctx:exit("TRUE") end -- BC_MONSTEROPEN.scr:106
end

return script
