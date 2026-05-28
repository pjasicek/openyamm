-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SIXFIRES.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Anskrammainline.scr
-- By Timmy
-- checks to see if the player has killed everything in anskram keep
script.labels["Onuse"] = function(ctx)
    -- SIXFIRES.scr:13
    -- NOTE this script just completes the quest right now.
    -- this is the routine where additional functionality should go
    if not ctx:hasKey(102) then -- SIXFIRES.scr:18-19
        -- haskey 101 g_ntemp
        -- if (g_ntemp==1, )
        -- ^^don't forget to add that back in...checks to make sure you're on the quest
        ctx:giveKey(102) -- SIXFIRES.scr:23
        ctx:giveExp(5000) -- SIXFIRES.scr:24
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- SIXFIRES.scr:25
        do return ctx:exit("") end -- SIXFIRES.scr:26
        -- endif
    end -- SIXFIRES.scr:28
    do return ctx:exit("") end -- SIXFIRES.scr:29
end

script.labels["Main"] = function(ctx)
    -- SIXFIRES.scr:32
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onuse") -- SIXFIRES.scr:36
    do return ctx:exit("") end -- SIXFIRES.scr:37
end

return script
