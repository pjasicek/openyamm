-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SPAWNNJAM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- SpawnNjam.scr
-- timmy
-- spawns Njam in the 1000 terrors
-- 1/21/02
-- flag variables
script.labels["DeleteAllNjams"] = function(ctx)
    -- SPAWNNJAM.scr:30
    ctx:object("NjamSpawnMarker0"):trigger("KillNjam") -- SPAWNNJAM.scr:33-34
    ctx:object("NjamSpawnMarker1"):trigger("KillNjam") -- SPAWNNJAM.scr:35-36
    ctx:object("NjamSpawnMarker2"):trigger("KillNjam") -- SPAWNNJAM.scr:37-38
    ctx:object("NjamSpawnMarker3"):trigger("KillNjam") -- SPAWNNJAM.scr:39-40
    ctx:object("NjamSpawnMarker4"):trigger("KillNjam") -- SPAWNNJAM.scr:41-42
    ctx:object("NjamSpawnMarker5"):trigger("KillNjam") -- SPAWNNJAM.scr:43-44
    ctx:object("NjamSpawnMarker6"):trigger("KillNjam") -- SPAWNNJAM.scr:45-46
    do return ctx:exit("") end -- SPAWNNJAM.scr:47
end

script.labels["Onspawn"] = function(ctx)
    -- SPAWNNJAM.scr:51
    ctx:getParam(0, "g_hobject") -- SPAWNNJAM.scr:54
    mm9.gosub(script, ctx, "DeleteAllNjams") -- SPAWNNJAM.scr:56
    ctx:object("g_hobject"):remove() -- SPAWNNJAM.scr:58
    ctx:wait(1, 1, "OnSpawn2") -- SPAWNNJAM.scr:59
    -- gosub Onspawn2
    do return ctx:exit("") end -- SPAWNNJAM.scr:61
end

script.labels["Onspawn2"] = function(ctx)
    -- SPAWNNJAM.scr:65
    ctx:self():doClientFx("GreaterDemon") -- SPAWNNJAM.scr:68
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNNJAM.scr:69
    ctx:wait(2, 2, "Appear") -- SPAWNNJAM.scr:70
    do return ctx:exit("") end -- SPAWNNJAM.scr:71
end

script.labels["BreakLink"] = function(ctx)
    -- SPAWNNJAM.scr:74
    ctx:state().nLinked = false -- SPAWNNJAM.scr:77
    do return ctx:exit("") end -- SPAWNNJAM.scr:78
end

script.labels["Appear"] = function(ctx)
    -- SPAWNNJAM.scr:80
    -- play appear effect here
    ctx:playSound("\\Sounds\\spells\\TownPortal.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNNJAM.scr:84
    ctx:state().XPos, ctx:state().YPos, ctx:state().ZPos = ctx:self():pos() -- SPAWNNJAM.scr:85
    ctx:state().hNjam = ctx:spawn("Xpos", "YPos", "ZPos", "sNjam") -- SPAWNNJAM.scr:86
    ctx:self():link(ctx:object("hNjam")) -- SPAWNNJAM.scr:87
    ctx:onEvent("OnObjectLinkBroken", "BreakLink") -- SPAWNNJAM.scr:88
    ctx:state().nLinked = true -- SPAWNNJAM.scr:89
    ctx:randomInt(20, 60, "g_ntemp") -- SPAWNNJAM.scr:90
    ctx:wait(2, "g_ntemp", "Vanish2") -- SPAWNNJAM.scr:91
    do return ctx:exit("") end -- SPAWNNJAM.scr:92
end

script.labels["Vanish2"] = function(ctx)
    -- SPAWNNJAM.scr:95
    if ctx:condition("nLinked==FALSE") then -- SPAWNNJAM.scr:98
        do return ctx:exit("") end -- SPAWNNJAM.scr:99
    end -- SPAWNNJAM.scr:100
    -- play vanish effect here
    ctx:object("hNjam"):doClientFx("GreaterDemon") -- SPAWNNJAM.scr:103
    ctx:playSound("\\Sounds\\magic\\Windup10.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNNJAM.scr:104
    ctx:wait(1, 1, "Vanish2b") -- SPAWNNJAM.scr:105
    do return ctx:exit("") end -- SPAWNNJAM.scr:106
end

script.labels["Vanish2b"] = function(ctx)
    -- SPAWNNJAM.scr:109
    ctx:object("hNjam"):setFlag("visible", false) -- SPAWNNJAM.scr:112
    ctx:playSound("\\Sounds\\magic\\teleport.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SPAWNNJAM.scr:113
    ctx:wait(1, 1, "Vanish2c") -- SPAWNNJAM.scr:114
    do return ctx:exit("") end -- SPAWNNJAM.scr:115
end

script.labels["Vanish2c"] = function(ctx)
    -- SPAWNNJAM.scr:119
    if ctx:condition("nLinked==TRUE") then -- SPAWNNJAM.scr:122
        ctx:object("hNjam"):remove() -- SPAWNNJAM.scr:123
    end -- SPAWNNJAM.scr:124
    do return ctx:exit("") end -- SPAWNNJAM.scr:125
end

script.labels["Init"] = function(ctx)
    -- SPAWNNJAM.scr:128
    if ctx:hasKey(108) then -- SPAWNNJAM.scr:133-134
        ctx:object("TriggerNjam0"):trigger("On") -- SPAWNNJAM.scr:135-136
        ctx:object("TriggerNjam1"):trigger("On") -- SPAWNNJAM.scr:137-138
        ctx:object("TriggerNjam2"):trigger("On") -- SPAWNNJAM.scr:139-140
        ctx:object("TriggerNjam3"):trigger("On") -- SPAWNNJAM.scr:141-142
        ctx:object("TriggerNjam4"):trigger("On") -- SPAWNNJAM.scr:143-144
        -- getobjecthandle TriggerNjam5 g_hobject
        -- trigger g_hobject On
        ctx:object("TriggerNjam6"):trigger("On") -- SPAWNNJAM.scr:147-148
        ctx:object("TriggerNjam7"):trigger("On") -- SPAWNNJAM.scr:149-150
        do return ctx:exit("") end -- SPAWNNJAM.scr:151
    else -- SPAWNNJAM.scr:152
        ctx:object("TriggerNjam0"):trigger("Off") -- SPAWNNJAM.scr:153-154
        ctx:object("TriggerNjam1"):trigger("Off") -- SPAWNNJAM.scr:155-156
        ctx:object("TriggerNjam2"):trigger("Off") -- SPAWNNJAM.scr:157-158
        ctx:object("TriggerNjam3"):trigger("Off") -- SPAWNNJAM.scr:159-160
        ctx:object("TriggerNjam4"):trigger("Off") -- SPAWNNJAM.scr:161-162
        -- getobjecthandle TriggerNjam5 g_hobject
        -- trigger g_hobject Off
        ctx:object("TriggerNjam6"):trigger("Off") -- SPAWNNJAM.scr:165-166
        ctx:object("TriggerNjam7"):trigger("Off") -- SPAWNNJAM.scr:167-168
        do return ctx:exit("") end -- SPAWNNJAM.scr:169
    end -- SPAWNNJAM.scr:170
    do return ctx:exit("") end -- SPAWNNJAM.scr:171
end

script.labels["Main"] = function(ctx)
    -- SPAWNNJAM.scr:175
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Spawn", "Onspawn") -- SPAWNNJAM.scr:180
    ctx:addTrigger("KillNjam", "Vanish2c") -- SPAWNNJAM.scr:181
    ctx:set("sNjam", "sNjam + Script") -- SPAWNNJAM.scr:182
    ctx:onEvent("OnPostStartWorld", "Init") -- SPAWNNJAM.scr:183
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- SPAWNNJAM.scr:184
    ctx:onEvent("OnPostSaveLoad", "Init") -- SPAWNNJAM.scr:185
    ctx:wait(1, .1, "Init") -- SPAWNNJAM.scr:186
    do return ctx:exit("") end -- SPAWNNJAM.scr:187
end

return script
