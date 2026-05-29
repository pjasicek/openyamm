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
    ctx:self():stop() -- ARENAVICTORY.scr:18
    ctx:takeKey(1017) -- ARENAVICTORY.scr:19
    ctx:wait(1, 3, "StartWin") -- ARENAVICTORY.scr:20
    do return ctx:exit("") end -- ARENAVICTORY.scr:21
end

script.labels["StartWin"] = function(ctx)
    -- ARENAVICTORY.scr:24
    -- onfoundtarget OnFoundTarget 56
    ctx:state().g_hobject = ctx:objectOrNil("Marker2") -- ARENAVICTORY.scr:28
    ctx:self():setTarget(ctx:object("g_hObject")) -- ARENAVICTORY.scr:29
    ctx:self():walkTo(ctx:object("g_hobject"), 8, "OnVictory") -- ARENAVICTORY.scr:30
    do return ctx:exit("") end -- ARENAVICTORY.scr:31
end

script.labels["DoTaunt"] = function(ctx)
    -- ARENAVICTORY.scr:36
    ctx:self():taunt("DoRunAway") -- ARENAVICTORY.scr:38
    do return ctx:exit("") end -- ARENAVICTORY.scr:39
end

script.labels["DoRunAway"] = function(ctx)
    -- ARENAVICTORY.scr:42
    ctx:wait(22, 0.5, "RunAway") -- ARENAVICTORY.scr:44
    do return ctx:exit("") end -- ARENAVICTORY.scr:45
end

script.labels["TauntAgain"] = function(ctx)
    -- ARENAVICTORY.scr:48
    ctx:state().dirX, ctx:state().dirY, ctx:state().dirZ = ctx:self():rotation() -- ARENAVICTORY.scr:56
    ctx:randomInt(0, 1, "random") -- ARENAVICTORY.scr:57
    ctx:state().dirX, ctx:state().dirY, ctx:state().dirZ = ctx:rotateDir("dirX", "dirY", "dirZ", 180) -- ARENAVICTORY.scr:59
    ctx:self():faceDir("dirX", "dirY", "dirZ", 450, "DoTaunt") -- ARENAVICTORY.scr:61
    do return ctx:exit("") end -- ARENAVICTORY.scr:63
end

script.labels["TauntLoopStop"] = function(ctx)
    -- ARENAVICTORY.scr:66
    ctx:self():stop() -- ARENAVICTORY.scr:68
    ctx:wait(22, 0, "DoNothing") -- ARENAVICTORY.scr:69
    do return ctx:exit("") end -- ARENAVICTORY.scr:70
end

script.labels["OnVictory"] = function(ctx)
    -- ARENAVICTORY.scr:73
    ctx:self():stop() -- ARENAVICTORY.scr:76
    ctx:self():taunt() -- ARENAVICTORY.scr:77
    ctx:wait(22, 1.5, "TauntAgain") -- ARENAVICTORY.scr:78
    do return ctx:exit("TRUE") end -- ARENAVICTORY.scr:80
end

script.labels["RunAway"] = function(ctx)
    -- ARENAVICTORY.scr:84
    ctx:state().g_hobject = ctx:objectOrNil("Marker1") -- ARENAVICTORY.scr:86
    ctx:self():setTarget(ctx:object("g_hObject")) -- ARENAVICTORY.scr:87
    ctx:self():runTo(ctx:object("g_hobject"), 2, "Delete") -- ARENAVICTORY.scr:88
    ctx:object("RotatingDoor2"):trigger("unlock") -- ARENAVICTORY.scr:90-91
    ctx:object("RotatingDoor2"):trigger("Use") -- ARENAVICTORY.scr:93-94
    ctx:object("RotatingDoor0"):trigger("unlock") -- ARENAVICTORY.scr:96-97
    ctx:object("RotatingDoor1"):trigger("unlock") -- ARENAVICTORY.scr:99-100
    do return ctx:exit("") end -- ARENAVICTORY.scr:101
    ctx:wait(24, 10, "Delete") -- ARENAVICTORY.scr:103
    do return ctx:exit("") end -- ARENAVICTORY.scr:105
end

script.labels["Delete"] = function(ctx)
    -- ARENAVICTORY.scr:109
    ctx:takeKey(1011) -- ARENAVICTORY.scr:112
    ctx:object("ShopkeeperElfMaleB0"):trigger("Pick") -- ARENAVICTORY.scr:114-115
    ctx:self():remove() -- ARENAVICTORY.scr:118
    do return ctx:exit("") end -- ARENAVICTORY.scr:120
end

script.labels["Main"] = function(ctx)
    -- ARENAVICTORY.scr:125
    -- Don't Forget to Delete this!
    mm9.gosub(script, ctx, "basedoorinit") -- ARENAVICTORY.scr:132
    ctx:wait(1, 1, "OnWin") -- ARENAVICTORY.scr:133
    -- tRACEon
    do return ctx:exit("") end -- ARENAVICTORY.scr:138
end

return script
