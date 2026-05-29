-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CRONAKIGA.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- CronaKiga.scr
-- By Timmy
-- gives the player the Crona Kiga
-- and the related key
-- Sigmund's RudeID is 87
-- SJR
-- SJR
script.labels["Onuse"] = function(ctx)
    -- CRONAKIGA.scr:20
    -- SJR
    if ctx:condition("hTrigger==0") then -- CRONAKIGA.scr:23
        ctx:state().hTrigger = ctx:objectOrNil("sTriggerName") -- CRONAKIGA.scr:24
    end -- CRONAKIGA.scr:25
    if ctx:condition("hTrigger!=0") then -- CRONAKIGA.scr:26
        ctx:trigger("hTrigger", "trigger") -- CRONAKIGA.scr:27
    end -- CRONAKIGA.scr:28
    -- SJR
    -- checks to see if player talked to Ludwig first
    ctx:hasKey(46, "g_ntemp") -- CRONAKIGA.scr:32
    if ctx:condition("g_ntemp==1") then -- CRONAKIGA.scr:34
        -- checks to see if player has picked up the mauscript already
        ctx:hasKey(48, "keycheck") -- CRONAKIGA.scr:36
        if ctx:condition("keycheck==0") then -- CRONAKIGA.scr:37
            -- gives player finished quest key
            ctx:giveKey("", 48) -- CRONAKIGA.scr:39
            -- this is where the manuscript should be removed and added to inventory
            ctx:removeTrigger("Use") -- CRONAKIGA.scr:46
            ctx:giveItem(390) -- CRONAKIGA.scr:48
            ctx:giveExp(10000) -- CRONAKIGA.scr:49
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- CRONAKIGA.scr:50
            -- SJR
            -- gotta wait to remove object for the
            -- mummy trigger to be sent
            ctx:wait(0, 1, "RemoveMe") -- CRONAKIGA.scr:54
            -- SJR
            do return ctx:exit(1) end -- CRONAKIGA.scr:56
        end -- CRONAKIGA.scr:58
    end -- CRONAKIGA.scr:59
    -- checks to see if player already picked up the manuscript
    ctx:hasKey(169, "keycheck") -- CRONAKIGA.scr:60
    if ctx:condition("keycheck==0") then -- CRONAKIGA.scr:61
        ctx:giveKey("", 169) -- CRONAKIGA.scr:63
        -- this is where the CronaKiga is removed and added to inventory
        ctx:giveItem(390) -- CRONAKIGA.scr:68
        ctx:giveExp(10000) -- CRONAKIGA.scr:69
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- CRONAKIGA.scr:70
        ctx:removeTrigger("Use") -- CRONAKIGA.scr:72
        -- SJR
        -- gotta wait to remove object for the
        -- mummy trigger to be sent
        ctx:wait(0, 1, "RemoveMe") -- CRONAKIGA.scr:77
        -- SJR
    end -- CRONAKIGA.scr:79
    do return ctx:exit(1) end -- CRONAKIGA.scr:82
end

-- SJR
script.labels["RemoveMe"] = function(ctx)
    -- CRONAKIGA.scr:86
    ctx:state().g_hObject = ctx:self() -- CRONAKIGA.scr:88
    ctx:object("g_hobject"):remove() -- CRONAKIGA.scr:89
    do return ctx:exit(1) end -- CRONAKIGA.scr:90
end

-- SJR
script.labels["Main"] = function(ctx)
    -- CRONAKIGA.scr:94
    -- SJR
    ctx:getParam(0, "sTriggerName") -- CRONAKIGA.scr:97
    -- SJR
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- CRONAKIGA.scr:101
    ctx:hasKey(48, "keycheck") -- CRONAKIGA.scr:102
    if ctx:condition("g_ntemp==1") then -- CRONAKIGA.scr:103
        ctx:state().g_hobject = ctx:objectOrNil("CronaKiga") -- CRONAKIGA.scr:104
        ctx:object("g_hobject"):remove() -- CRONAKIGA.scr:105
        ctx:exitScript() -- CRONAKIGA.scr:106
        do return ctx:exit("") end -- CRONAKIGA.scr:107
    end -- CRONAKIGA.scr:108
    ctx:hasKey(169, "keycheck") -- CRONAKIGA.scr:110
    if ctx:condition("g_ntemp==1") then -- CRONAKIGA.scr:111
        ctx:state().g_hobject = ctx:objectOrNil("CronaKiga") -- CRONAKIGA.scr:112
        ctx:object("g_hobject"):remove() -- CRONAKIGA.scr:113
        ctx:exitScript() -- CRONAKIGA.scr:114
        do return ctx:exit("") end -- CRONAKIGA.scr:115
    end -- CRONAKIGA.scr:116
    do return ctx:exit(1) end -- CRONAKIGA.scr:117
end

return script
