-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "NPC50.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 8, path = "globals.inc" }

-- NPC49.scr
-- By Timmy
-- handles In'jorg's giving It'lor a job
-- checks to see if a sound is currently playing
-- handler for sounds
-- duration of sound
-- if sound is done this is true
-- handler for second actor
script.labels["Onblabber"] = function(ctx)
    -- NPC50.scr:18
    -- erccs blabber
    ctx:playSound("voices\\NPC\\NPC_050.wav", "Onexit", 100, 240, "FALSE", 100) -- NPC50.scr:25
    do return ctx:exit("") end -- NPC50.scr:30
end

script.labels["Onexit"] = function(ctx)
    -- NPC50.scr:36
    do return ctx:exit("") end -- NPC50.scr:39
end

script.labels["Main"] = function(ctx)
    -- NPC50.scr:42
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onblabber") -- NPC50.scr:46
    -- AddTrigger Use, OnUse ; ADD THIS BACK IN WHEN PROPS CAN REACT TO WAIT COMMAND
    ctx:cacheSound("voices\\NPC\\NPC_050.wav") -- NPC50.scr:48
    do return ctx:exit("") end -- NPC50.scr:51
end

return script
