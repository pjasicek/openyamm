-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RETAINER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "NPCBase.Inc" }

-- retainer.scr
-- timmy
-- handles the retainer stuff
-- edited by Bones -- 6/11/03
-- TELP Patch 1.3 -- oorrects Arienh A'Klindor & Sowelu Axeldotir behavior.
-- #include globals.inc
-- flag variables
script.labels["OnRude"] = function(ctx)
    -- RETAINER.scr:21
    do return ctx:exit("") end -- RETAINER.scr:24
end

script.labels["OnUse"] = function(ctx)
    -- RETAINER.scr:28
    ctx:playSound("sound", "Onexit", 100, 240, "FALSE", 100) -- RETAINER.scr:31
    do return ctx:exit("") end -- RETAINER.scr:32
end

script.labels["OnExit"] = function(ctx)
    -- RETAINER.scr:35
    do return ctx:exit("") end -- RETAINER.scr:38
end

script.labels["Init"] = function(ctx)
    -- RETAINER.scr:41
    ctx:state().g_hobject = ctx:self() -- RETAINER.scr:44
    if not ctx:hasKey("nKey") then -- RETAINER.scr:46-47
        ctx:self():setFlag("visible", true) -- RETAINER.scr:48
        ctx:self():setFlag("solid", true) -- RETAINER.scr:49
        ctx:self():setFlag("gravity", true) -- RETAINER.scr:50
        mm9.gosub(script, ctx, "NPCBaseInit") -- RETAINER.scr:51
    else -- RETAINER.scr:52
        ctx:object("g_hobject"):setFlag("visible", false) -- RETAINER.scr:53
        ctx:object("g_hobject"):setFlag("solid", false) -- RETAINER.scr:54
        ctx:object("g_hobject"):setFlag("gravity", false) -- RETAINER.scr:55
        do return ctx:exit("") end -- RETAINER.scr:56
    end -- RETAINER.scr:57
    do return ctx:exit("") end -- RETAINER.scr:58
end

script.labels["Main"] = function(ctx)
    -- RETAINER.scr:61
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "sound") -- RETAINER.scr:66
    ctx:getParam(1, "nKey") -- RETAINER.scr:67
    ctx:onEvent("OnPostStartWorld", "Init") -- RETAINER.scr:69
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- RETAINER.scr:70
    ctx:onEvent("OnPostSaveLoad", "Init") -- RETAINER.scr:71
    ctx:wait(1, .1, "Init") -- RETAINER.scr:72
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- RETAINER.scr:73
    ctx:addTrigger("Use", "OnUse") -- RETAINER.scr:74
    do return ctx:exit("") end -- RETAINER.scr:75
end

script.labels["Init"] = function(ctx)
    -- RETAINER.scr:78
    -- overloaded -- Bones
    ctx:state().g_sPad2 = ctx:self():name() -- RETAINER.scr:84
    ctx:state().g_sTemp = 238 -- RETAINER.scr:85
    if ctx:condition("g_sPad2 == g_sTemp") then -- RETAINER.scr:86
        ctx:set("sound", "voices\\npc\\NPC_238.wav") -- RETAINER.scr:87
        ctx:state().nKey = 460 -- RETAINER.scr:88
    end -- RETAINER.scr:89
    if ctx:condition("nKey == 453") then -- RETAINER.scr:91
        ctx:state().nKey = 452 -- RETAINER.scr:92
    end -- RETAINER.scr:93
    do return mm9.gotoLabel(script, ctx, "Init") end -- RETAINER.scr:95
end

return script
