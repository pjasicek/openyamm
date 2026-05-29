-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HONKIES.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "basewander.inc" }

-- Honkies.scr
-- timmy
-- handles Kira honky quest
-- is this guy walking to the dock.
script.labels["OnRude"] = function(ctx)
    -- HONKIES.scr:23
    ctx:state().g_ncounter = 0 -- HONKIES.scr:26
    if ctx:hasKey(145) then -- HONKIES.scr:28-29
        if ctx:hasKey(142) then -- HONKIES.scr:31-32
            mm9.gosub(script, ctx, "Walk") -- HONKIES.scr:33
            ctx:state().g_ncounter = (tonumber(ctx:state().g_ncounter) or 0) + 1 -- HONKIES.scr:34
        end -- HONKIES.scr:35
        if ctx:hasKey(143) then -- HONKIES.scr:37-38
            mm9.gosub(script, ctx, "Walk") -- HONKIES.scr:39
            ctx:state().g_ncounter = (tonumber(ctx:state().g_ncounter) or 0) + 1 -- HONKIES.scr:40
        end -- HONKIES.scr:41
        if ctx:hasKey(144) then -- HONKIES.scr:43-44
            mm9.gosub(script, ctx, "Walk") -- HONKIES.scr:45
            ctx:state().g_ncounter = (tonumber(ctx:state().g_ncounter) or 0) + 1 -- HONKIES.scr:46
        end -- HONKIES.scr:47
    end -- HONKIES.scr:48
    if ctx:condition("g_ncounter==3") then -- HONKIES.scr:50
        mm9.gosub(script, ctx, "Reward") -- HONKIES.scr:51
        do return ctx:exit("") end -- HONKIES.scr:52
    end -- HONKIES.scr:53
    do return ctx:exit("") end -- HONKIES.scr:54
end

script.labels["Reward"] = function(ctx)
    -- HONKIES.scr:58
    -- ...........success.............
    if ctx:hasKey(77) then -- HONKIES.scr:64-65
        do return ctx:exit("") end -- HONKIES.scr:66
    end -- HONKIES.scr:67
    ctx:giveKey(77) -- HONKIES.scr:69
    ctx:giveExp(8000) -- HONKIES.scr:70
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- HONKIES.scr:71
    ctx:state().BeenDone = true -- HONKIES.scr:72
    do return ctx:exit("") end -- HONKIES.scr:74
end

script.labels["killme"] = function(ctx)
    -- HONKIES.scr:77
    ctx:exitScript() -- HONKIES.scr:81
    do return ctx:exit("") end -- HONKIES.scr:82
end

script.labels["Walk"] = function(ctx)
    -- HONKIES.scr:86
    if ctx:condition("walk==0") then -- HONKIES.scr:89
        -- ......walk (run!) to dock info goes here!!!
        ctx:self():stop() -- HONKIES.scr:91
        mm9.gosub(script, ctx, "BaseWanderStop") -- HONKIES.scr:92
        ctx:state().g_hobject = ctx:objectOrNil("HonkyMarker") -- HONKIES.scr:93
        ctx:self():runTo(ctx:object("g_hobject"), 16, "OnShanghai") -- HONKIES.scr:94
        ctx:state().walk = 1 -- HONKIES.scr:95
        do return ctx:exit("") end -- HONKIES.scr:96
    end -- HONKIES.scr:97
    do return ctx:exit("") end -- HONKIES.scr:99
end

script.labels["OnShanghai"] = function(ctx)
    -- HONKIES.scr:102
    ctx:self():remove() -- HONKIES.scr:105
    do return ctx:exit("") end -- HONKIES.scr:106
end

script.labels["OnUse"] = function(ctx)
    -- HONKIES.scr:110
    ctx:self():stop() -- HONKIES.scr:113
    mm9.gosub(script, ctx, "basewanderstop") -- HONKIES.scr:114
    ctx:getParam(0, "g_hobject") -- HONKIES.scr:115
    ctx:self():faceObject(ctx:object("g_hobject"), 200, "DoNothing") -- HONKIES.scr:116
    ctx:doRude("nNPC_ID") -- HONKIES.scr:117
    do return ctx:exit("") end -- HONKIES.scr:118
end

script.labels["Init"] = function(ctx)
    -- HONKIES.scr:121
    ctx:self():attachProp("Prop_Name", "Skin_Name", "Socket_Name", ctx:object("g_hobject2")) -- HONKIES.scr:124
    if ctx:hasKey(77) then -- HONKIES.scr:126-127
        mm9.gosub(script, ctx, "OnShanghai") -- HONKIES.scr:128
        do return ctx:exit("") end -- HONKIES.scr:129
    end -- HONKIES.scr:130
    do return ctx:exit("") end -- HONKIES.scr:132
end

script.labels["Main"] = function(ctx)
    -- HONKIES.scr:136
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "nNPC_ID") -- HONKIES.scr:141
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- HONKIES.scr:143
    ctx:addTrigger("Use", "OnUse") -- HONKIES.scr:145
    mm9.gosub(script, ctx, "BaseWanderInit") -- HONKIES.scr:146
    ctx:onEvent("OnPostStartWorld", "Init") -- HONKIES.scr:147
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- HONKIES.scr:148
    -- OnPostSaveLoad Init
    ctx:wait(1, .1, "Init") -- HONKIES.scr:150
    do return ctx:exit("") end -- HONKIES.scr:151
end

return script
