-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC284.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "baseMelee.inc" }

-- NPC284.scr
-- timmy
-- handles Robert Aefgil voice and stuff
-- flag variables
script.labels["Init"] = function(ctx)
    -- NPC284.scr:18
    if ctx:hasKey(255) then -- NPC284.scr:22-23
        ctx:self():remove() -- NPC284.scr:25
        do return ctx:exit("") end -- NPC284.scr:26
    end -- NPC284.scr:27
    ctx:hasKey(254, "g_ntemp") -- NPC284.scr:29
    if ctx:condition("g_ntemp==0") then -- NPC284.scr:31
        ctx:state().g_hobject = ctx:self() -- NPC284.scr:32
        ctx:self():setFlag("visible", false) -- NPC284.scr:33
        ctx:self():setFlag("solid", false) -- NPC284.scr:34
        ctx:self():setFlag("gravity", false) -- NPC284.scr:35
        do return ctx:exit("") end -- NPC284.scr:36
    end -- NPC284.scr:37
    mm9.gosub(script, ctx, "baseWanderInit") -- NPC284.scr:39
    do return ctx:exit("") end -- NPC284.scr:41
end

script.labels["Appear"] = function(ctx)
    -- NPC284.scr:44
    if ctx:hasKey(255) then -- NPC284.scr:47-48
        do return ctx:exit("") end -- NPC284.scr:49
    end -- NPC284.scr:50
    if ctx:hasKey(254) then -- NPC284.scr:52-53
        ctx:state().g_hobject = ctx:self() -- NPC284.scr:54
        ctx:self():setFlag("visible", true) -- NPC284.scr:55
        ctx:self():setFlag("solid", true) -- NPC284.scr:56
        ctx:self():setFlag("gravity", true) -- NPC284.scr:57
        do return ctx:exit("") end -- NPC284.scr:58
    end -- NPC284.scr:59
    do return ctx:exit("") end -- NPC284.scr:60
end

script.labels["OnUse"] = function(ctx)
    -- NPC284.scr:63
    ctx:self():stop() -- NPC284.scr:66
    mm9.gosub(script, ctx, "BaseWanderStop") -- NPC284.scr:67
    ctx:getParam(0, "g_hobject") -- NPC284.scr:68
    ctx:self():faceObject(ctx:object("g_hobject"), 240, "DoNothing") -- NPC284.scr:69
    ctx:doRude(284) -- NPC284.scr:70
    ctx:playSound("voices\\NPC\\NPC_284.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC284.scr:71
    do return ctx:exit("") end -- NPC284.scr:72
end

script.labels["OnRude"] = function(ctx)
    -- NPC284.scr:75
    mm9.gosub(script, ctx, "BaseWanderStart") -- NPC284.scr:78
    do return ctx:exit("") end -- NPC284.scr:79
end

script.labels["OnExit"] = function(ctx)
    -- NPC284.scr:82
    do return ctx:exit("") end -- NPC284.scr:85
end

script.labels["Main"] = function(ctx)
    -- NPC284.scr:88
    -- traceon
    -- Don't Forget to Delete this!
    ctx:atTime(6, 0, "Appear", "Appear") -- NPC284.scr:93
    ctx:addTrigger("Use", "OnUse") -- NPC284.scr:94
    ctx:addTrigger("Appear", "Appear") -- NPC284.scr:95
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- NPC284.scr:96
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC284.scr:97
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC284.scr:98
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC284.scr:99
    ctx:wait(1, .1, "Init") -- NPC284.scr:100
    do return ctx:exit("") end -- NPC284.scr:102
end

return script
