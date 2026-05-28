-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SVENARENA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "BaseMelee.inc" }

-- SvenArena.scr
-- timmy
-- handles sven's behavior in arena
-- flag variables
script.labels["OnWalk"] = function(ctx)
    -- SVENARENA.scr:20
    if ctx:hasKey(231) then -- SVENARENA.scr:25-26
        do return ctx:exit("") end -- SVENARENA.scr:27
    end -- SVENARENA.scr:28
    if not ctx:hasKey(230) then -- SVENARENA.scr:30-31
        do return ctx:exit("") end -- SVENARENA.scr:32
    end -- SVENARENA.scr:33
    ctx:command("getmyhandle", "g_hobject") -- SVENARENA.scr:35
    ctx:command("setflag", "g_hobject, visible") -- SVENARENA.scr:36
    ctx:command("setflag", "g_hobject, solid") -- SVENARENA.scr:37
    ctx:command("setflag", "g_hobject, gravity") -- SVENARENA.scr:38
    if ctx:condition("bGuard==FALSE") then -- SVENARENA.scr:40
        ctx:command("getobjecthandle", "ClanSoldier1 g_hobject") -- SVENARENA.scr:41
        ctx:trigger("g_hobject", "Guard") -- SVENARENA.scr:42
        ctx:command("getobjecthandle", "ClanSoldier0 g_hobject") -- SVENARENA.scr:44
        ctx:trigger("g_hobject", "Guard") -- SVENARENA.scr:45
        ctx:command("getobjecthandle", "sMarker g_hobject") -- SVENARENA.scr:47
        ctx:command("walkto", "g_hobject 6 OnArrive") -- SVENARENA.scr:48
        ctx:command("playsound", "sounds\\events\\Trumpets02.wav, DoNothing, 100, 24000, FALSE, 100") -- SVENARENA.scr:50
    end -- SVENARENA.scr:51
    do return ctx:exit("") end -- SVENARENA.scr:53
end

script.labels["OnGuard"] = function(ctx)
    -- SVENARENA.scr:56
    ctx:command("getmyhandle", "g_hobject") -- SVENARENA.scr:60
    ctx:command("setflag", "g_hobject, visible") -- SVENARENA.scr:61
    ctx:command("setflag", "g_hobject, solid") -- SVENARENA.scr:62
    ctx:command("setflag", "g_hobject, gravity") -- SVENARENA.scr:63
    ctx:command("getobjecthandle", "sMarker g_hobject") -- SVENARENA.scr:64
    ctx:command("walkto", "g_hobject 6 OnArrive") -- SVENARENA.scr:65
    do return ctx:exit("") end -- SVENARENA.scr:66
end

script.labels["OnArrive"] = function(ctx)
    -- SVENARENA.scr:68
    ctx:command("wait", "1 2 OnWave") -- SVENARENA.scr:72
    do return ctx:exit("") end -- SVENARENA.scr:73
end

script.labels["OnWave"] = function(ctx)
    -- SVENARENA.scr:76
    if ctx:condition("bGuard==FALSE") then -- SVENARENA.scr:79
        ctx:command("getobjecthandle", "WinCheerTrigger0 g_hobject") -- SVENARENA.scr:80
        ctx:trigger("g_hobject", "trigger") -- SVENARENA.scr:81
    end -- SVENARENA.scr:82
    ctx:command("playanim", "Bless DoNothing") -- SVENARENA.scr:84
    ctx:command("wait", "1 2 OnStart") -- SVENARENA.scr:85
    do return ctx:exit("") end -- SVENARENA.scr:86
end

script.labels["Init"] = function(ctx)
    -- SVENARENA.scr:91
    ctx:command("getmyhandle", "g_hobject") -- SVENARENA.scr:95
    ctx:command("clearflag", "g_hobject, visible") -- SVENARENA.scr:96
    ctx:command("clearflag", "g_hobject, solid") -- SVENARENA.scr:97
    ctx:command("clearflag", "g_hobject, gravity") -- SVENARENA.scr:98
    do return ctx:exit("") end -- SVENARENA.scr:99
end

script.labels["OnStart"] = function(ctx)
    -- SVENARENA.scr:103
    ctx:command("getobjecthandle", "RotatingDoor4 g_hobject") -- SVENARENA.scr:106
    ctx:trigger("g_hobject", "use") -- SVENARENA.scr:107
    ctx:command("getobjecthandle", "CommonerHuman2MaleB0 g_hobject") -- SVENARENA.scr:108
    ctx:trigger("g_hobject", "enter") -- SVENARENA.scr:109
    ctx:command("wait", "1 1 Boo") -- SVENARENA.scr:110
    do return ctx:exit("") end -- SVENARENA.scr:112
end

script.labels["Boo"] = function(ctx)
    -- SVENARENA.scr:115
    if ctx:condition("bGuard==FALSE") then -- SVENARENA.scr:118
        ctx:command("getobjecthandle", "LooseBooTrigger0 g_hobject") -- SVENARENA.scr:119
        ctx:trigger("g_hobject", "trigger") -- SVENARENA.scr:120
    end -- SVENARENA.scr:121
    do return ctx:exit("") end -- SVENARENA.scr:123
end

script.labels["OnUse"] = function(ctx)
    -- SVENARENA.scr:127
    ctx:giveKey(1034) -- SVENARENA.scr:130
    do return ctx:exit("") end -- SVENARENA.scr:131
end

script.labels["OnRude"] = function(ctx)
    -- SVENARENA.scr:134
    ctx:takeKey(1034) -- SVENARENA.scr:137
    do return ctx:exit("") end -- SVENARENA.scr:138
end

script.labels["Main"] = function(ctx)
    -- SVENARENA.scr:143
    -- traceon
    -- Don't Forget to Delete this!
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- SVENARENA.scr:149
    ctx:addTrigger("Walk", "OnWalk") -- SVENARENA.scr:150
    ctx:addTrigger("use", "OnUse") -- SVENARENA.scr:151
    ctx:addTrigger("Guard", "OnGuard") -- SVENARENA.scr:152
    ctx:getParam(0, "sMarker") -- SVENARENA.scr:153
    ctx:getParam(1, "bGuard") -- SVENARENA.scr:154
    mm9.gosub(script, ctx, "Init") -- SVENARENA.scr:155
    do return ctx:exit("") end -- SVENARENA.scr:156
end

return script
