-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MINE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Mine.scr
-- By Timmy
-- Edited by Bones
-- TELP Patch 1.3 -- de-activated
script.labels["Onuse"] = function(ctx)
    -- MINE.scr:14
    -- NOTE this script just completes the quest right now.
    do return ctx:exit("") end -- MINE.scr:18
    -- checks to see if player has done this yet
    ctx:hasKey(37, "g_ntemp") -- MINE.scr:20
    if ctx:condition("g_ntemp==0") then -- MINE.scr:22
        -- checks to see if player is on Quest
        ctx:hasKey(3, "keycheck") -- MINE.scr:23
        if ctx:condition("keycheck==1") then -- MINE.scr:24
            ctx:giveKey("", 35) -- MINE.scr:26
            -- gives player finished quest key
            ctx:giveKey("", 36) -- MINE.scr:27
            ctx:giveKey("", 37) -- MINE.scr:28
            ctx:giveExp(1000) -- MINE.scr:30
            do return ctx:exit("") end -- MINE.scr:31
        end -- MINE.scr:32
    end -- MINE.scr:33
    do return ctx:exit("") end -- MINE.scr:35
end

script.labels["Main"] = function(ctx)
    -- MINE.scr:38
    -- TraceOn ;delete me!!
    do return ctx:exit("") end -- MINE.scr:43
    ctx:addTrigger("Use", "Onuse") -- MINE.scr:45
    ctx:addTrigger("destroy", "Onuse") -- MINE.scr:46
    do return ctx:exit("") end -- MINE.scr:47
end

return script
