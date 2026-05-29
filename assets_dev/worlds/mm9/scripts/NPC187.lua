-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC187.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- NPC187.scr
-- timmy
-- handles Hungerda Atlidotir voice and quest stuff
-- Parameters
-- P0 name of wav file
-- P1 name of animation to run
-- P2  # of times animation runs
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- NPC187.scr:28
    ctx:randomInt(1, 2, "g_ntemp") -- NPC187.scr:31
    if ctx:condition("g_ntemp==1") then -- NPC187.scr:33
        ctx:playSound("voices\\NPC\\NPC_187a.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC187.scr:34
        do return ctx:exit("") end -- NPC187.scr:35
    end -- NPC187.scr:36
    if ctx:condition("g_ntemp==2") then -- NPC187.scr:38
        ctx:playSound("voices\\NPC\\NPC_187b.wav", "DoNothing", 100, 240, "FALSE", 100) -- NPC187.scr:39
        do return ctx:exit("") end -- NPC187.scr:40
    end -- NPC187.scr:41
    do return ctx:exit("") end -- NPC187.scr:45
end

script.labels["OnReturn"] = function(ctx)
    -- NPC187.scr:50
    ctx:state().g_hobject = ctx:objectOrNil("Atlimarker0") -- NPC187.scr:53
    ctx:self():walkTo(ctx:object("g_hobject"), 256, "DoNothing") -- NPC187.scr:54
    do return ctx:exit("") end -- NPC187.scr:55
    do return ctx:exit("") end -- NPC187.scr:57
end

script.labels["OnArrive"] = function(ctx)
    -- NPC187.scr:60
    if ctx:hasKey(197) then -- NPC187.scr:63-64
        ctx:state().g_hobject = ctx:objectOrNil("AtliMarker") -- NPC187.scr:65
        ctx:self():walkTo(ctx:object("g_hobject"), 256, "DoNothing") -- NPC187.scr:66
        do return ctx:exit("") end -- NPC187.scr:67
    end -- NPC187.scr:68
    do return ctx:exit("") end -- NPC187.scr:69
end

script.labels["Init"] = function(ctx)
    -- NPC187.scr:71
    if ctx:hasKey(127) then -- NPC187.scr:74-75
        ctx:state().g_hobject = ctx:self() -- NPC187.scr:77
        ctx:self():setFlag("visible", false) -- NPC187.scr:78
        ctx:self():setFlag("solid", false) -- NPC187.scr:79
        ctx:self():setFlag("gravity", false) -- NPC187.scr:80
        do return ctx:exit("") end -- NPC187.scr:81
    end -- NPC187.scr:83
    do return ctx:exit("") end -- NPC187.scr:86
end

script.labels["Main"] = function(ctx)
    -- NPC187.scr:89
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- NPC187.scr:97
    ctx:addTrigger("Return", "OnReturn") -- NPC187.scr:98
    ctx:onEvent("OnPostStartWorld", "Init") -- NPC187.scr:99
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- NPC187.scr:100
    ctx:onEvent("OnPostSaveLoad", "Init") -- NPC187.scr:101
    ctx:wait(1, .1, "Init") -- NPC187.scr:102
    do return ctx:exit("") end -- NPC187.scr:103
end

return script
