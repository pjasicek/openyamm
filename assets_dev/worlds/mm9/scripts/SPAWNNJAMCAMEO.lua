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
    ctx:wait(1, 1, "OnSpawn2") -- SPAWNNJAMCAMEO.scr:41
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:42
end

script.labels["Onspawn2"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:46
    ctx:self():doClientFx("GreaterDemon") -- SPAWNNJAMCAMEO.scr:49
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNNJAMCAMEO.scr:50
    ctx:wait(1, 2, "Appear") -- SPAWNNJAMCAMEO.scr:51
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:52
end

script.labels["BreakLink"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:55
    ctx:state().nLinked = false -- SPAWNNJAMCAMEO.scr:58
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:59
end

script.labels["Appear"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:61
    -- play appear effect here
    ctx:playSound("\\Sounds\\spells\\TownPortal.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNNJAMCAMEO.scr:65
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:self():pos() -- SPAWNNJAMCAMEO.scr:66
    ctx:state().hNjam = ctx:spawn("Xpos", "YPos", "ZPos", "sNjam") -- SPAWNNJAMCAMEO.scr:67
    ctx:self():link(ctx:object("hNjam")) -- SPAWNNJAMCAMEO.scr:68
    ctx:onEvent("OnObjectLinkBroken", "BreakLink") -- SPAWNNJAMCAMEO.scr:69
    ctx:state().nLinked = true -- SPAWNNJAMCAMEO.scr:70
    ctx:randomInt(10, 20, "g_ntemp") -- SPAWNNJAMCAMEO.scr:71
    ctx:wait(2, "g_ntemp", "Vanish2") -- SPAWNNJAMCAMEO.scr:72
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:73
end

script.labels["Vanish2"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:76
    if ctx:condition("nLinked==FALSE") then -- SPAWNNJAMCAMEO.scr:79
        do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:80
    end -- SPAWNNJAMCAMEO.scr:81
    -- play vanish effect here
    ctx:object("hNjam"):doClientFx("GreaterDemon") -- SPAWNNJAMCAMEO.scr:84
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNNJAMCAMEO.scr:85
    ctx:wait(1, 1, "Vanish2b") -- SPAWNNJAMCAMEO.scr:86
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:87
end

script.labels["Vanish2b"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:90
    ctx:object("hNjam"):setFlag("visible", false) -- SPAWNNJAMCAMEO.scr:93
    ctx:playSound("\\Sounds\\magic\\teleport.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNNJAMCAMEO.scr:94
    ctx:wait(1, 1, "Vanish2c") -- SPAWNNJAMCAMEO.scr:95
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:96
end

script.labels["Vanish2c"] = function(ctx)
    -- SPAWNNJAMCAMEO.scr:100
    if ctx:condition("nLinked==TRUE") then -- SPAWNNJAMCAMEO.scr:103
        ctx:object("hNjam"):remove() -- SPAWNNJAMCAMEO.scr:104
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
    ctx:set("sNjam", "sNjam + Script") -- SPAWNNJAMCAMEO.scr:124
    ctx:onEvent("OnPostStartWorld", "Init") -- SPAWNNJAMCAMEO.scr:125
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- SPAWNNJAMCAMEO.scr:126
    ctx:onEvent("OnPostSaveLoad", "Init") -- SPAWNNJAMCAMEO.scr:127
    ctx:wait(1, .1, "Init") -- SPAWNNJAMCAMEO.scr:128
    do return ctx:exit("") end -- SPAWNNJAMCAMEO.scr:129
end

return script
