-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RANDVERRETAINER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- forad.scr
-- By Timmy
-- handles forad's stuff
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
-- handler for second actor
-- flag variables
script.labels["Onblabber"] = function(ctx)
    -- RANDVERRETAINER.scr:22
    -- erccs blabber
    ctx:playSound("voices\\NPC\\NPC_085.wav", "Onexit", 100, 240, "FALSE", 100) -- RANDVERRETAINER.scr:29
    do return ctx:exit("") end -- RANDVERRETAINER.scr:34
end

script.labels["Init"] = function(ctx)
    -- RANDVERRETAINER.scr:37
    -- LoopAnim Sitting 0 DoNothing
    ctx:state().g_hobject = ctx:self() -- RANDVERRETAINER.scr:41
    if not ctx:hasKey(453) then -- RANDVERRETAINER.scr:44-45
        ctx:self():setFlag("visible", true) -- RANDVERRETAINER.scr:48
        ctx:self():setFlag("solid", true) -- RANDVERRETAINER.scr:49
        ctx:self():setFlag("gravity", true) -- RANDVERRETAINER.scr:50
        ctx:self():loopAnimation("sitting", 0, "DoNothing") -- RANDVERRETAINER.scr:51
        do return ctx:exit("") end -- RANDVERRETAINER.scr:52
    else -- RANDVERRETAINER.scr:53
        ctx:object("g_hobject"):setFlag("visible", false) -- RANDVERRETAINER.scr:54
        ctx:object("g_hobject"):setFlag("solid", false) -- RANDVERRETAINER.scr:55
        ctx:object("g_hobject"):setFlag("gravity", false) -- RANDVERRETAINER.scr:56
        do return ctx:exit("") end -- RANDVERRETAINER.scr:57
    end -- RANDVERRETAINER.scr:58
    do return ctx:exit("") end -- RANDVERRETAINER.scr:60
end

script.labels["Onexit"] = function(ctx)
    -- RANDVERRETAINER.scr:65
    do return ctx:exit("") end -- RANDVERRETAINER.scr:68
end

script.labels["Main"] = function(ctx)
    -- RANDVERRETAINER.scr:71
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onblabber") -- RANDVERRETAINER.scr:75
    ctx:onEvent("OnPostStartWorld", "Init") -- RANDVERRETAINER.scr:76
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- RANDVERRETAINER.scr:77
    ctx:onEvent("OnPostSaveLoad", "Init") -- RANDVERRETAINER.scr:78
    ctx:wait(1, .1, "Init") -- RANDVERRETAINER.scr:79
    do return ctx:exit("") end -- RANDVERRETAINER.scr:80
end

return script
