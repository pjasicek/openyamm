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
    ctx:command("getobjecthandle", "NjamSpawnMarker0 g_hobject") -- SPAWNNJAM.scr:33
    ctx:trigger("g_hobject", "KillNjam") -- SPAWNNJAM.scr:34
    ctx:command("getobjecthandle", "NjamSpawnMarker1 g_hobject") -- SPAWNNJAM.scr:35
    ctx:trigger("g_hobject", "KillNjam") -- SPAWNNJAM.scr:36
    ctx:command("getobjecthandle", "NjamSpawnMarker2 g_hobject") -- SPAWNNJAM.scr:37
    ctx:trigger("g_hobject", "KillNjam") -- SPAWNNJAM.scr:38
    ctx:command("getobjecthandle", "NjamSpawnMarker3 g_hobject") -- SPAWNNJAM.scr:39
    ctx:trigger("g_hobject", "KillNjam") -- SPAWNNJAM.scr:40
    ctx:command("getobjecthandle", "NjamSpawnMarker4 g_hobject") -- SPAWNNJAM.scr:41
    ctx:trigger("g_hobject", "KillNjam") -- SPAWNNJAM.scr:42
    ctx:command("getobjecthandle", "NjamSpawnMarker5 g_hobject") -- SPAWNNJAM.scr:43
    ctx:trigger("g_hobject", "KillNjam") -- SPAWNNJAM.scr:44
    ctx:command("getobjecthandle", "NjamSpawnMarker6 g_hobject") -- SPAWNNJAM.scr:45
    ctx:trigger("g_hobject", "KillNjam") -- SPAWNNJAM.scr:46
    do return ctx:exit("") end -- SPAWNNJAM.scr:47
end

script.labels["Onspawn"] = function(ctx)
    -- SPAWNNJAM.scr:51
    ctx:getParam(0, "g_hobject") -- SPAWNNJAM.scr:54
    mm9.gosub(script, ctx, "DeleteAllNjams") -- SPAWNNJAM.scr:56
    ctx:command("removeobject", "g_hobject") -- SPAWNNJAM.scr:58
    ctx:command("wait", "1 1 OnSpawn2") -- SPAWNNJAM.scr:59
    -- gosub Onspawn2
    do return ctx:exit("") end -- SPAWNNJAM.scr:61
end

script.labels["Onspawn2"] = function(ctx)
    -- SPAWNNJAM.scr:65
    ctx:command("getmyhandle", "g_hmyobject") -- SPAWNNJAM.scr:67
    ctx:command("doclientfx", "g_hMyObject,GreaterDemon") -- SPAWNNJAM.scr:68
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNNJAM.scr:69
    ctx:command("wait", "2 2 Appear") -- SPAWNNJAM.scr:70
    do return ctx:exit("") end -- SPAWNNJAM.scr:71
end

script.labels["BreakLink"] = function(ctx)
    -- SPAWNNJAM.scr:74
    ctx:command("set", "nLinked, FALSE") -- SPAWNNJAM.scr:77
    do return ctx:exit("") end -- SPAWNNJAM.scr:78
end

script.labels["Appear"] = function(ctx)
    -- SPAWNNJAM.scr:80
    -- play appear effect here
    ctx:command("playsound", "\\Sounds\\spells\\TownPortal.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNNJAM.scr:84
    ctx:command("getpos", "g_hmyobject XPos YPos ZPos") -- SPAWNNJAM.scr:85
    ctx:command("spawn", "hNjam Xpos YPos ZPos sNjam") -- SPAWNNJAM.scr:86
    ctx:command("createobjectlink", "hNjam") -- SPAWNNJAM.scr:87
    ctx:command("onobjectlinkbroken", "BreakLink") -- SPAWNNJAM.scr:88
    ctx:command("set", "nLinked, TRUE") -- SPAWNNJAM.scr:89
    ctx:command("getrandomint", "20 60 g_ntemp") -- SPAWNNJAM.scr:90
    ctx:command("wait", "2 g_ntemp Vanish2") -- SPAWNNJAM.scr:91
    do return ctx:exit("") end -- SPAWNNJAM.scr:92
end

script.labels["Vanish2"] = function(ctx)
    -- SPAWNNJAM.scr:95
    if ctx:condition("nLinked==FALSE") then -- SPAWNNJAM.scr:98
        do return ctx:exit("") end -- SPAWNNJAM.scr:99
    end -- SPAWNNJAM.scr:100
    -- play vanish effect here
    ctx:command("doclientfx", "hNjam,GreaterDemon") -- SPAWNNJAM.scr:103
    ctx:command("playsound", "\\Sounds\\magic\\Windup10.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNNJAM.scr:104
    ctx:command("wait", "1 1 Vanish2b") -- SPAWNNJAM.scr:105
    do return ctx:exit("") end -- SPAWNNJAM.scr:106
end

script.labels["Vanish2b"] = function(ctx)
    -- SPAWNNJAM.scr:109
    ctx:command("clearflag", "hNjam visible") -- SPAWNNJAM.scr:112
    ctx:command("playsound", "\\Sounds\\magic\\teleport.wav, DoNothing, 100, 24000, FALSE, 100") -- SPAWNNJAM.scr:113
    ctx:command("wait", "1 1 Vanish2c") -- SPAWNNJAM.scr:114
    do return ctx:exit("") end -- SPAWNNJAM.scr:115
end

script.labels["Vanish2c"] = function(ctx)
    -- SPAWNNJAM.scr:119
    if ctx:condition("nLinked==TRUE") then -- SPAWNNJAM.scr:122
        ctx:command("removeobject", "hNjam") -- SPAWNNJAM.scr:123
    end -- SPAWNNJAM.scr:124
    do return ctx:exit("") end -- SPAWNNJAM.scr:125
end

script.labels["Init"] = function(ctx)
    -- SPAWNNJAM.scr:128
    if ctx:hasKey(108) then -- SPAWNNJAM.scr:133-134
        ctx:command("getobjecthandle", "TriggerNjam0 g_hobject") -- SPAWNNJAM.scr:135
        ctx:trigger("g_hobject", "On") -- SPAWNNJAM.scr:136
        ctx:command("getobjecthandle", "TriggerNjam1 g_hobject") -- SPAWNNJAM.scr:137
        ctx:trigger("g_hobject", "On") -- SPAWNNJAM.scr:138
        ctx:command("getobjecthandle", "TriggerNjam2 g_hobject") -- SPAWNNJAM.scr:139
        ctx:trigger("g_hobject", "On") -- SPAWNNJAM.scr:140
        ctx:command("getobjecthandle", "TriggerNjam3 g_hobject") -- SPAWNNJAM.scr:141
        ctx:trigger("g_hobject", "On") -- SPAWNNJAM.scr:142
        ctx:command("getobjecthandle", "TriggerNjam4 g_hobject") -- SPAWNNJAM.scr:143
        ctx:trigger("g_hobject", "On") -- SPAWNNJAM.scr:144
        -- getobjecthandle TriggerNjam5 g_hobject
        -- trigger g_hobject On
        ctx:command("getobjecthandle", "TriggerNjam6 g_hobject") -- SPAWNNJAM.scr:147
        ctx:trigger("g_hobject", "On") -- SPAWNNJAM.scr:148
        ctx:command("getobjecthandle", "TriggerNjam7 g_hobject") -- SPAWNNJAM.scr:149
        ctx:trigger("g_hobject", "On") -- SPAWNNJAM.scr:150
        do return ctx:exit("") end -- SPAWNNJAM.scr:151
    else -- SPAWNNJAM.scr:152
        ctx:command("getobjecthandle", "TriggerNjam0 g_hobject") -- SPAWNNJAM.scr:153
        ctx:trigger("g_hobject", "Off") -- SPAWNNJAM.scr:154
        ctx:command("getobjecthandle", "TriggerNjam1 g_hobject") -- SPAWNNJAM.scr:155
        ctx:trigger("g_hobject", "Off") -- SPAWNNJAM.scr:156
        ctx:command("getobjecthandle", "TriggerNjam2 g_hobject") -- SPAWNNJAM.scr:157
        ctx:trigger("g_hobject", "Off") -- SPAWNNJAM.scr:158
        ctx:command("getobjecthandle", "TriggerNjam3 g_hobject") -- SPAWNNJAM.scr:159
        ctx:trigger("g_hobject", "Off") -- SPAWNNJAM.scr:160
        ctx:command("getobjecthandle", "TriggerNjam4 g_hobject") -- SPAWNNJAM.scr:161
        ctx:trigger("g_hobject", "Off") -- SPAWNNJAM.scr:162
        -- getobjecthandle TriggerNjam5 g_hobject
        -- trigger g_hobject Off
        ctx:command("getobjecthandle", "TriggerNjam6 g_hobject") -- SPAWNNJAM.scr:165
        ctx:trigger("g_hobject", "Off") -- SPAWNNJAM.scr:166
        ctx:command("getobjecthandle", "TriggerNjam7 g_hobject") -- SPAWNNJAM.scr:167
        ctx:trigger("g_hobject", "Off") -- SPAWNNJAM.scr:168
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
    ctx:command("snjam", "= sNjam + Script") -- SPAWNNJAM.scr:182
    ctx:command("onpoststartworld", "Init") -- SPAWNNJAM.scr:183
    ctx:command("onpostminisaveload", "Init") -- SPAWNNJAM.scr:184
    ctx:command("onpostsaveload", "Init") -- SPAWNNJAM.scr:185
    ctx:command("wait", "1 .1 Init") -- SPAWNNJAM.scr:186
    do return ctx:exit("") end -- SPAWNNJAM.scr:187
end

return script
