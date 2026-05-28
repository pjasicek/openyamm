-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPAWNNJAMCAMEO.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- SpawnNjam.scr
-- timmy
-- spawns Njam in the 1000 terrors
-- 1/21/02
-- flag variables
script.labels["DeleteAllNjams"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:30
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:33
end

script.labels["Onspawn"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:37
    mm9.gosub(script, ctx, "DeleteAllNjams") -- SPAWNNJAMCAMEO.scr:40
    ctx:command("wait", "1 1 OnSpawn2") -- SPAWNNJAMCAMEO.scr:41
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:42
end

script.labels["Onspawn2"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:46
    ctx:command("getmyhandle", "g_hmyobject") -- SPAWNNJAMCAMEO.scr:48
    ctx:command("doclientfx", "g_hMyObject,GreaterDemon") -- SPAWNNJAMCAMEO.scr:49
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNNJAMCAMEO.scr:50
    ctx:command("wait", "1 2 Appear") -- SPAWNNJAMCAMEO.scr:51
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:52
end

script.labels["BreakLink"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:55
    ctx:command("set", "nLinked, FALSE") -- SPAWNNJAMCAMEO.scr:58
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:59
end

script.labels["Appear"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:61
    -- play appear effect here
    ctx:command("playsound", "\\Sounds\\spells\\TownPortal.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNNJAMCAMEO.scr:65
    ctx:command("getpos", "g_hmyobject XPos YPos ZPos") -- SPAWNNJAMCAMEO.scr:66
    ctx:command("spawn", "hNjam Xpos YPos ZPos sNjam") -- SPAWNNJAMCAMEO.scr:67
    ctx:command("createobjectlink", "hNjam") -- SPAWNNJAMCAMEO.scr:68
    ctx:command("onobjectlinkbroken", "BreakLink") -- SPAWNNJAMCAMEO.scr:69
    ctx:command("set", "nLinked, TRUE") -- SPAWNNJAMCAMEO.scr:70
    ctx:command("getrandomint", "10 20 g_ntemp") -- SPAWNNJAMCAMEO.scr:71
    ctx:command("wait", "2 g_ntemp Vanish2") -- SPAWNNJAMCAMEO.scr:72
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:73
end

script.labels["Vanish2"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:76
    if ctx:condition("nLinked==FALSE") then -- SPAWNNJAMCAMEO.scr:79
        do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:80
    end -- SPAWNNJAMCAMEO.scr:81
    -- play vanish effect here
    ctx:command("doclientfx", "hNjam,GreaterDemon") -- SPAWNNJAMCAMEO.scr:84
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNNJAMCAMEO.scr:85
    ctx:command("wait", "1 1 Vanish2b") -- SPAWNNJAMCAMEO.scr:86
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:87
end

script.labels["Vanish2b"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:90
    ctx:command("clearflag", "hNjam visible") -- SPAWNNJAMCAMEO.scr:93
    ctx:command("playsound", "\\Sounds\\magic\\teleport.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNNJAMCAMEO.scr:94
    ctx:command("wait", "1 1 Vanish2c") -- SPAWNNJAMCAMEO.scr:95
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:96
end

script.labels["Vanish2c"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:100
    if ctx:condition("nLinked==TRUE") then -- SPAWNNJAMCAMEO.scr:103
        ctx:command("removeobject", "hNjam") -- SPAWNNJAMCAMEO.scr:104
    end -- SPAWNNJAMCAMEO.scr:105
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:106
end

script.labels["Init"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:109
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:113
end

script.labels["Main"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:117
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Spawn", "Onspawn") -- SPAWNNJAMCAMEO.scr:122
    ctx:addTrigger("KillNjam", "Vanish2c") -- SPAWNNJAMCAMEO.scr:123
    ctx:command("snjam", "= sNjam + Script") -- SPAWNNJAMCAMEO.scr:124
    ctx:command("onpoststartworld", "Init") -- SPAWNNJAMCAMEO.scr:125
    ctx:command("onpostminisaveload", "Init") -- SPAWNNJAMCAMEO.scr:126
    ctx:command("onpostsaveload", "Init") -- SPAWNNJAMCAMEO.scr:127
    ctx:command("wait", "1 .1 Init") -- SPAWNNJAMCAMEO.scr:128
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:129
end

return script
