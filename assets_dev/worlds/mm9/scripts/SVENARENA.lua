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
    ctx:state().g_hobject = ctx:self() -- SVENARENA.scr:35
    ctx:self():setFlag("visible", true) -- SVENARENA.scr:36
    ctx:self():setFlag("solid", true) -- SVENARENA.scr:37
    ctx:self():setFlag("gravity", true) -- SVENARENA.scr:38
    if ctx:condition("bGuard==FALSE") then -- SVENARENA.scr:40
        ctx:object("ClanSoldier1"):trigger("Guard") -- SVENARENA.scr:41-42
        ctx:object("ClanSoldier0"):trigger("Guard") -- SVENARENA.scr:44-45
        ctx:state().g_hobject = ctx:objectOrNil("sMarker") -- SVENARENA.scr:47
        ctx:self():walkTo(ctx:object("g_hobject"), 6, "OnArrive") -- SVENARENA.scr:48
        ctx:playSound("sounds\\events\\Trumpets02.wav", "DoNothing", 100, 24000, "FALSE", 100) -- SVENARENA.scr:50
    end -- SVENARENA.scr:51
    do return ctx:exit("") end -- SVENARENA.scr:53
end

script.labels["OnGuard"] = function(ctx)
    -- SVENARENA.scr:56
    ctx:state().g_hobject = ctx:self() -- SVENARENA.scr:60
    ctx:self():setFlag("visible", true) -- SVENARENA.scr:61
    ctx:self():setFlag("solid", true) -- SVENARENA.scr:62
    ctx:self():setFlag("gravity", true) -- SVENARENA.scr:63
    ctx:state().g_hobject = ctx:objectOrNil("sMarker") -- SVENARENA.scr:64
    ctx:self():walkTo(ctx:object("g_hobject"), 6, "OnArrive") -- SVENARENA.scr:65
    do return ctx:exit("") end -- SVENARENA.scr:66
end

script.labels["OnArrive"] = function(ctx)
    -- SVENARENA.scr:68
    ctx:wait(1, 2, "OnWave") -- SVENARENA.scr:72
    do return ctx:exit("") end -- SVENARENA.scr:73
end

script.labels["OnWave"] = function(ctx)
    -- SVENARENA.scr:76
    if ctx:condition("bGuard==FALSE") then -- SVENARENA.scr:79
        ctx:object("WinCheerTrigger0"):trigger("trigger") -- SVENARENA.scr:80-81
    end -- SVENARENA.scr:82
    ctx:self():playAnimation("Bless", "DoNothing") -- SVENARENA.scr:84
    ctx:wait(1, 2, "OnStart") -- SVENARENA.scr:85
    do return ctx:exit("") end -- SVENARENA.scr:86
end

script.labels["Init"] = function(ctx)
    -- SVENARENA.scr:91
    ctx:state().g_hobject = ctx:self() -- SVENARENA.scr:95
    ctx:self():setFlag("visible", false) -- SVENARENA.scr:96
    ctx:self():setFlag("solid", false) -- SVENARENA.scr:97
    ctx:self():setFlag("gravity", false) -- SVENARENA.scr:98
    do return ctx:exit("") end -- SVENARENA.scr:99
end

script.labels["OnStart"] = function(ctx)
    -- SVENARENA.scr:103
    ctx:object("RotatingDoor4"):trigger("use") -- SVENARENA.scr:106-107
    ctx:object("CommonerHuman2MaleB0"):trigger("enter") -- SVENARENA.scr:108-109
    ctx:wait(1, 1, "Boo") -- SVENARENA.scr:110
    do return ctx:exit("") end -- SVENARENA.scr:112
end

script.labels["Boo"] = function(ctx)
    -- SVENARENA.scr:115
    if ctx:condition("bGuard==FALSE") then -- SVENARENA.scr:118
        ctx:object("LooseBooTrigger0"):trigger("trigger") -- SVENARENA.scr:119-120
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
