-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TM_HARDROCK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 16, path = "globals.inc" }

-- tm_Hardrock.scr
-- Brett Yagi
-- This script is used to award the hard rock quest
-- to the player if they destroy all the hard rock
-- Parameters
-- 0 - number of destructable brushes before quest is complete
-- 1 - number of key to give
-- 2 - amount of experience to give for successful completion.
script.labels["dn"] = function(ctx)
    -- TM_HARDROCK.scr:23
    do return ctx:exit(1) end -- TM_HARDROCK.scr:25
end

script.labels["OneDown"] = function(ctx)
    -- TM_HARDROCK.scr:29
    -- Callback to "OneDown" trigger which counts the amount of
    -- Destructable brushes destroyed until it gets to
    -- nHardRockPieces upon which quest is complete
    ctx:set("count", "count + 1") -- TM_HARDROCK.scr:36
    if ctx:condition("count == nHardRockPieces") then -- TM_HARDROCK.scr:37
        ctx:giveKey("nHardRockKey") -- TM_HARDROCK.scr:38
        ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240000, "FALSE", 100) -- TM_HARDROCK.scr:39
        if ctx:condition("nHardRockKey==36") then -- TM_HARDROCK.scr:42
            -- LDG ebora addition
            -- send a message to ebora
            ctx:object("Ebora"):trigger("FreeAtLast") -- TM_HARDROCK.scr:45-46
        end -- TM_HARDROCK.scr:47
        if ctx:condition("nExperience!=0") then -- TM_HARDROCK.scr:49
            ctx:giveExp("nExperience") -- TM_HARDROCK.scr:50
        end -- TM_HARDROCK.scr:52
    end -- TM_HARDROCK.scr:53
    do return ctx:exit(1) end -- TM_HARDROCK.scr:54
end

script.labels["Main"] = function(ctx)
    -- TM_HARDROCK.scr:58
    -- Traceon
    ctx:getParam(0, "nHardRockPieces") -- TM_HARDROCK.scr:62
    ctx:getParam(1, "nHardRockKey") -- TM_HARDROCK.scr:63
    ctx:getParam(2, "nExperience") -- TM_HARDROCK.scr:64
    ctx:addTrigger("OneDown", "OneDown") -- TM_HARDROCK.scr:65
    do return ctx:exit(1) end -- TM_HARDROCK.scr:67
end

return script
