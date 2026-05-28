-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARENACREATURE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basedoor.inc" }

-- ArenaCreature.scr
-- timmy
-- handles scholar promo stuff
script.labels["OnArrive"] = function(ctx)
    -- ARENACREATURE.scr:20
    ctx:command("stop", "") -- ARENACREATURE.scr:24
    ctx:command("taunt", "OnStartFight") -- ARENACREATURE.scr:26
    -- wait 1 2 OnStartFight
    do return ctx:exit("TRUE") end -- ARENACREATURE.scr:29
end

script.labels["OnStartFight"] = function(ctx)
    -- ARENACREATURE.scr:32
    ctx:command("getobjecthandle", "ShopkeeperElfMaleB0 g_hobject") -- ARENACREATURE.scr:35
    ctx:trigger("g_hobject", "Arrive") -- ARENACREATURE.scr:36
    do return ctx:exit("") end -- ARENACREATURE.scr:38
end

script.labels["Init"] = function(ctx)
    -- ARENACREATURE.scr:41
    ctx:command("getmyhandle", "g_hmyobject") -- ARENACREATURE.scr:44
    ctx:command("getstat", "g_hmyobject HitPoints g_ntemp") -- ARENACREATURE.scr:45
    ctx:command("nminhp", "= g_ntemp * .7") -- ARENACREATURE.scr:46
    ctx:command("nmaxhp", "= g_ntemp * 1.5") -- ARENACREATURE.scr:47
    ctx:command("getrandomint", "nMinHP, nMaxHP, nHitPoints") -- ARENACREATURE.scr:48
    ctx:command("setstat", "g_hmyobject Hitpoints nHitPoints") -- ARENACREATURE.scr:49
    ctx:command("setstat", "g_hmyobject GaveTreasure TRUE") -- ARENACREATURE.scr:50
    ctx:command("getobjecthandle", "RotatingDoor2,g_hObject") -- ARENACREATURE.scr:52
    ctx:trigger("g_hObject", "Unlock") -- ARENACREATURE.scr:53
    ctx:trigger("g_hObject", "Use") -- ARENACREATURE.scr:54
    ctx:command("getobjecthandle", "RotatingDoor4,g_hObject") -- ARENACREATURE.scr:56
    ctx:trigger("g_hObject", "Unlock") -- ARENACREATURE.scr:57
    ctx:trigger("g_hObject", "Use") -- ARENACREATURE.scr:58
    ctx:command("wait", "29,2.2,GetOutThere") -- ARENACREATURE.scr:60
    do return ctx:exit("") end -- ARENACREATURE.scr:62
end

script.labels["GetOutThere"] = function(ctx)
    -- ARENACREATURE.scr:65
    ctx:command("getobjecthandle", "marker2 g_hobject") -- ARENACREATURE.scr:68
    ctx:command("target", "g_hObject") -- ARENACREATURE.scr:69
    ctx:command("runto", "g_hobject 128 OnArrive") -- ARENACREATURE.scr:71
    do return ctx:exit("") end -- ARENACREATURE.scr:72
end

script.labels["OnHate"] = function(ctx)
    -- ARENACREATURE.scr:76
    ctx:command("addenemy", "AIBase") -- ARENACREATURE.scr:79
    ctx:command("addfriend", "Player") -- ARENACREATURE.scr:80
    ctx:command("getstatstr", "g_hmyobject,ScriptName,sScript") -- ARENACREATURE.scr:84
    -- cprint running script
    -- cprint sScript
    ctx:command("getobjecthandle", "RotatingDoor2,g_hObject") -- ARENACREATURE.scr:88
    ctx:trigger("g_hObject", "close") -- ARENACREATURE.scr:89
    ctx:trigger("g_hObject", "lock") -- ARENACREATURE.scr:90
    ctx:command("getobjecthandle", "RotatingDoor4,g_hObject") -- ARENACREATURE.scr:92
    ctx:trigger("g_hObject", "close") -- ARENACREATURE.scr:93
    ctx:trigger("g_hObject", "lock") -- ARENACREATURE.scr:94
    ctx:command("runscript", "sScript") -- ARENACREATURE.scr:96
    do return ctx:exit("") end -- ARENACREATURE.scr:98
end

script.labels["FaceMarker"] = function(ctx)
    -- ARENACREATURE.scr:101
    ctx:command("getobjecthandle", "Marker2,g_hObject") -- ARENACREATURE.scr:104
    ctx:command("faceobject", "g_hObject,0") -- ARENACREATURE.scr:105
    do return ctx:exit("") end -- ARENACREATURE.scr:106
end

script.labels["Main"] = function(ctx)
    -- ARENACREATURE.scr:110
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sMonster_ID") -- ARENACREATURE.scr:115
    ctx:giveKey(1011) -- ARENACREATURE.scr:116
    ctx:addTrigger("HateAll", "OnHate") -- ARENACREATURE.scr:117
    ctx:command("wait", "2,0.1,FaceMarker") -- ARENACREATURE.scr:118
    ctx:command("wait", "1 3 Init") -- ARENACREATURE.scr:119
    mm9.gosub(script, ctx, "BaseDoorInit") -- ARENACREATURE.scr:121
    ctx:command("getmyhandle", "g_hmyobject") -- ARENACREATURE.scr:124
    ctx:command("setpropstring", "DeathTriggerTarget,ShopkeeperElfMaleB0") -- ARENACREATURE.scr:126
    ctx:command("setpropstring", "DeathTriggerMessage,IDied") -- ARENACREATURE.scr:127
    ctx:setPropNumber("RunAwayChance", 0) -- ARENACREATURE.scr:128
    ctx:setPropNumber("CanOpenDoors", 0) -- ARENACREATURE.scr:129
    ctx:command("getstatstr", "g_hmyobject,ScriptName,g_sTemp") -- ARENACREATURE.scr:131
    ctx:command("cachescript", "g_sTemp") -- ARENACREATURE.scr:133
    do return ctx:exit("") end -- ARENACREATURE.scr:136
end

return script
