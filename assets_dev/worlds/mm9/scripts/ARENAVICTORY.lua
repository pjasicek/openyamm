-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARENAVICTORY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basedoor.inc" }

-- ArenaVictory.scr
-- timmy
-- handles scholar promo stuff
script.labels["OnWin"] = function(ctx)
    -- ARENAVICTORY.scr:14
    ctx:command("stop", "") -- ARENAVICTORY.scr:18
    ctx:takeKey(1017) -- ARENAVICTORY.scr:19
    ctx:command("wait", "1 3 StartWin") -- ARENAVICTORY.scr:20
    do return ctx:exit("") end -- ARENAVICTORY.scr:21
end

script.labels["StartWin"] = function(ctx)
    -- ARENAVICTORY.scr:24
    -- onfoundtarget OnFoundTarget 56
    ctx:command("getobjecthandle", "Marker2 g_hobject") -- ARENAVICTORY.scr:28
    ctx:command("target", "g_hObject,FALSE") -- ARENAVICTORY.scr:29
    ctx:command("walkto", "g_hobject 8 OnVictory") -- ARENAVICTORY.scr:30
    do return ctx:exit("") end -- ARENAVICTORY.scr:31
end

script.labels["DoTaunt"] = function(ctx)
    -- ARENAVICTORY.scr:36
    ctx:command("taunt", "DoRunAway") -- ARENAVICTORY.scr:38
    do return ctx:exit("") end -- ARENAVICTORY.scr:39
end

script.labels["DoRunAway"] = function(ctx)
    -- ARENAVICTORY.scr:42
    ctx:command("wait", "22,0.5,RunAway") -- ARENAVICTORY.scr:44
    do return ctx:exit("") end -- ARENAVICTORY.scr:45
end

script.labels["TauntAgain"] = function(ctx)
    -- ARENAVICTORY.scr:48
    ctx:command("getfacedir", "g_hmyobject,dirX,dirY,dirZ") -- ARENAVICTORY.scr:56
    ctx:command("getrandomint", "0,1,random") -- ARENAVICTORY.scr:57
    ctx:command("rotatedir", "dirX,dirY,dirZ,180") -- ARENAVICTORY.scr:59
    ctx:command("facedir", "dirX,dirY,dirZ,450,DoTaunt") -- ARENAVICTORY.scr:61
    do return ctx:exit("") end -- ARENAVICTORY.scr:63
end

script.labels["TauntLoopStop"] = function(ctx)
    -- ARENAVICTORY.scr:66
    ctx:command("stop", "") -- ARENAVICTORY.scr:68
    ctx:command("wait", "22,0,DoNothing") -- ARENAVICTORY.scr:69
    do return ctx:exit("") end -- ARENAVICTORY.scr:70
end

script.labels["OnVictory"] = function(ctx)
    -- ARENAVICTORY.scr:73
    ctx:command("stop", "") -- ARENAVICTORY.scr:76
    ctx:command("taunt", "") -- ARENAVICTORY.scr:77
    ctx:command("wait", "22,1.5,TauntAgain") -- ARENAVICTORY.scr:78
    do return ctx:exit("TRUE") end -- ARENAVICTORY.scr:80
end

script.labels["RunAway"] = function(ctx)
    -- ARENAVICTORY.scr:84
    ctx:command("getobjecthandle", "Marker1 g_hobject") -- ARENAVICTORY.scr:86
    ctx:command("target", "g_hObject,FALSE") -- ARENAVICTORY.scr:87
    ctx:command("runto", "g_hobject 2 Delete") -- ARENAVICTORY.scr:88
    ctx:command("getobjecthandle", "RotatingDoor2 g_hobject") -- ARENAVICTORY.scr:90
    ctx:trigger("g_hobject", "unlock") -- ARENAVICTORY.scr:91
    ctx:command("getobjecthandle", "RotatingDoor2,g_hObject") -- ARENAVICTORY.scr:93
    ctx:trigger("g_hObject", "Use") -- ARENAVICTORY.scr:94
    ctx:command("getobjecthandle", "RotatingDoor0 g_hobject") -- ARENAVICTORY.scr:96
    ctx:trigger("g_hobject", "unlock") -- ARENAVICTORY.scr:97
    ctx:command("getobjecthandle", "RotatingDoor1 g_hobject") -- ARENAVICTORY.scr:99
    ctx:trigger("g_hobject", "unlock") -- ARENAVICTORY.scr:100
    do return ctx:exit("") end -- ARENAVICTORY.scr:101
    ctx:command("wait", "24,10,Delete") -- ARENAVICTORY.scr:103
    do return ctx:exit("") end -- ARENAVICTORY.scr:105
end

script.labels["Delete"] = function(ctx)
    -- ARENAVICTORY.scr:109
    ctx:takeKey(1011) -- ARENAVICTORY.scr:112
    ctx:command("getobjecthandle", "ShopkeeperElfMaleB0 g_hobject") -- ARENAVICTORY.scr:114
    ctx:trigger("g_hobject", "Pick") -- ARENAVICTORY.scr:115
    ctx:command("getmyhandle", "g_hmyobject") -- ARENAVICTORY.scr:117
    ctx:command("removeobject", "g_hmyobject") -- ARENAVICTORY.scr:118
    do return ctx:exit("") end -- ARENAVICTORY.scr:120
end

script.labels["Main"] = function(ctx)
    -- ARENAVICTORY.scr:125
    -- Don't Forget to Delete this!
    ctx:command("getmyhandle", "g_hmyobject") -- ARENAVICTORY.scr:130
    mm9.gosub(script, ctx, "basedoorinit") -- ARENAVICTORY.scr:132
    ctx:command("wait", "1 1 OnWin") -- ARENAVICTORY.scr:133
    -- tRACEon
    do return ctx:exit("") end -- ARENAVICTORY.scr:138
end

return script
