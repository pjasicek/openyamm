-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SLAGEXTRACTOR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- SlagExtractor.scr
-- timmy
-- handles the slag extractor stuff.
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- SLAGEXTRACTOR.scr:23
    if not ctx:hasKey(9512) then -- SLAGEXTRACTOR.scr:26-27
        -- Cprint Player picked up the Slag extractor
        ctx:giveItem(398) -- SLAGEXTRACTOR.scr:31
        ctx:giveKey(9512) -- SLAGEXTRACTOR.scr:32
        ctx:state().g_hobject = ctx:self() -- SLAGEXTRACTOR.scr:33
        ctx:self():setFlag("visible", false) -- SLAGEXTRACTOR.scr:34
        -- clearflag g_hobject, solid
        -- clearflag g_hobject, gravity
        do return ctx:exit("") end -- SLAGEXTRACTOR.scr:37
    end -- SLAGEXTRACTOR.scr:38
end

-- No exit on purpose?
script.labels["OnShow"] = function(ctx)
    -- SLAGEXTRACTOR.scr:43
    -- Cprint Player is swapping slag extractor
    if ctx:hasKey(37) then -- SLAGEXTRACTOR.scr:49-50
        do return ctx:exit("") end -- SLAGEXTRACTOR.scr:51
    end -- SLAGEXTRACTOR.scr:52
    ctx:giveExp(5000) -- SLAGEXTRACTOR.scr:54
    ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- SLAGEXTRACTOR.scr:55
    ctx:self():setModelFilenames("model_name", "Model_skin") -- SLAGEXTRACTOR.scr:56
    ctx:takeItem(399) -- SLAGEXTRACTOR.scr:57
    ctx:giveKey(37) -- SLAGEXTRACTOR.scr:58
    ctx:state().g_hobject = ctx:self() -- SLAGEXTRACTOR.scr:59
    ctx:self():setFlag("visible", true) -- SLAGEXTRACTOR.scr:60
    -- setflag g_hobject, solid
    -- setflag g_hobject, gravity
    do return ctx:exit("") end -- SLAGEXTRACTOR.scr:64
end

script.labels["Init"] = function(ctx)
    -- SLAGEXTRACTOR.scr:67
    -- Cprint Ran Init!!
    if ctx:hasKey(9512) then -- SLAGEXTRACTOR.scr:72-73
        -- Cprint Player Got broken slag Extractor
        if ctx:hasKey(37) then -- SLAGEXTRACTOR.scr:77-78
            -- Cprint Set Model Filename because the player fixed the machine
            ctx:self():setModelFilenames("model_name", "Model_skin") -- SLAGEXTRACTOR.scr:82
            do return ctx:exit("") end -- SLAGEXTRACTOR.scr:83
        else -- SLAGEXTRACTOR.scr:84
            -- Cprint Extractor is not there because player picked it up already
            ctx:state().g_hobject = ctx:self() -- SLAGEXTRACTOR.scr:88
            ctx:self():setFlag("visible", false) -- SLAGEXTRACTOR.scr:89
            -- clearflag g_hobject, solid
            -- clearflag g_hobject, gravity
            do return ctx:exit("") end -- SLAGEXTRACTOR.scr:92
        end -- SLAGEXTRACTOR.scr:93
    end -- SLAGEXTRACTOR.scr:94
    do return ctx:exit("") end -- SLAGEXTRACTOR.scr:96
end

script.labels["Main"] = function(ctx)
    -- SLAGEXTRACTOR.scr:100
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- SLAGEXTRACTOR.scr:107
    ctx:addTrigger("Show", "OnShow") -- SLAGEXTRACTOR.scr:108
    ctx:onEvent("OnPostStartWorld", "Init") -- SLAGEXTRACTOR.scr:109
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- SLAGEXTRACTOR.scr:110
    ctx:onEvent("OnPostSaveLoad", "Init") -- SLAGEXTRACTOR.scr:111
    ctx:wait(1, .1, "Init") -- SLAGEXTRACTOR.scr:112
    do return ctx:exit("") end -- SLAGEXTRACTOR.scr:113
end

return script
