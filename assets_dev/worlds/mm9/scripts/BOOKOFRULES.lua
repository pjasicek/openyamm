-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BOOKOFRULES.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- BookOfRules.scr
-- By Timmy
-- gives the player the Book of rules
-- and the related key
-- Markel's RudeID is 127
script.labels["Onuse"] = function(ctx)
    -- BOOKOFRULES.scr:15
    -- checks to see if player talked to Ludwig first
    ctx:hasKey(57, "g_ntemp") -- BOOKOFRULES.scr:19
    if ctx:condition("g_ntemp==1") then -- BOOKOFRULES.scr:21
        -- checks to see if player has picked up the mauscript already
        ctx:hasKey(59, "keycheck") -- BOOKOFRULES.scr:23
        if ctx:condition("keycheck==0") then -- BOOKOFRULES.scr:24
            -- gives player finished quest key
            ctx:giveKey("", 59) -- BOOKOFRULES.scr:26
            -- this is where the manuscript should be removed and added to inventory
            ctx:giveItem(391) -- BOOKOFRULES.scr:32
            ctx:giveExp(5000) -- BOOKOFRULES.scr:33
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- BOOKOFRULES.scr:34
            ctx:state().g_hobject = ctx:objectOrNil("BookRules") -- BOOKOFRULES.scr:35
            ctx:object("g_hobject"):remove() -- BOOKOFRULES.scr:36
            do return ctx:exit("") end -- BOOKOFRULES.scr:37
        end -- BOOKOFRULES.scr:39
    end -- BOOKOFRULES.scr:40
    -- checks to see if player already picked up the manuscript
    ctx:hasKey(166, "keycheck") -- BOOKOFRULES.scr:41
    if ctx:condition("keycheck==0") then -- BOOKOFRULES.scr:42
        ctx:giveKey("", 166) -- BOOKOFRULES.scr:44
        ctx:state().keydata = 166 -- BOOKOFRULES.scr:45
        -- this is where the manuscript isremoved and added to inventory
        ctx:giveItem(391) -- BOOKOFRULES.scr:51
        ctx:giveExp(5000) -- BOOKOFRULES.scr:52
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- BOOKOFRULES.scr:53
        ctx:state().g_hobject = ctx:objectOrNil("BookRules") -- BOOKOFRULES.scr:54
        ctx:object("g_hobject"):remove() -- BOOKOFRULES.scr:55
    end -- BOOKOFRULES.scr:56
    do return ctx:exit("") end -- BOOKOFRULES.scr:59
end

script.labels["Main"] = function(ctx)
    -- BOOKOFRULES.scr:65
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- BOOKOFRULES.scr:69
    ctx:hasKey(59, "keycheck") -- BOOKOFRULES.scr:70
    if ctx:condition("g_ntemp==1") then -- BOOKOFRULES.scr:71
        ctx:state().g_hobject = ctx:objectOrNil("manuscript") -- BOOKOFRULES.scr:72
        ctx:object("g_hobject"):remove() -- BOOKOFRULES.scr:73
        ctx:exitScript() -- BOOKOFRULES.scr:74
        do return ctx:exit("") end -- BOOKOFRULES.scr:75
    end -- BOOKOFRULES.scr:76
    ctx:hasKey(166, "keycheck") -- BOOKOFRULES.scr:78
    if ctx:condition("g_ntemp==1") then -- BOOKOFRULES.scr:79
        ctx:state().g_hobject = ctx:objectOrNil("manuscript") -- BOOKOFRULES.scr:80
        ctx:object("g_hobject"):remove() -- BOOKOFRULES.scr:81
        ctx:exitScript() -- BOOKOFRULES.scr:82
        do return ctx:exit("") end -- BOOKOFRULES.scr:83
    end -- BOOKOFRULES.scr:84
    do return ctx:exit("") end -- BOOKOFRULES.scr:85
end

return script
