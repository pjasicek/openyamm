-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ANSKRAMMAINLINE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Anskrammainline.scr
-- By Timmy
-- checks to see if the player has killed everything in anskram keep
script.labels["Onuse"] = function(ctx)
    -- ANSKRAMMAINLINE.scr:15
    -- NOTE this script just completes the quest right now.
    -- this is the routine where additional functionality should go
    -- checks to see if player has done this yet
    ctx:hasKey(39, "g_ntemp") -- ANSKRAMMAINLINE.scr:19
    if ctx:condition("g_ntemp==0") then -- ANSKRAMMAINLINE.scr:21
        -- gives player finished quest key
        ctx:giveKey("", 39) -- ANSKRAMMAINLINE.scr:23
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- ANSKRAMMAINLINE.scr:24
        do return ctx:exit("") end -- ANSKRAMMAINLINE.scr:25
    end -- ANSKRAMMAINLINE.scr:26
    do return ctx:exit("") end -- ANSKRAMMAINLINE.scr:27
end

script.labels["Main"] = function(ctx)
    -- ANSKRAMMAINLINE.scr:33
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onuse") -- ANSKRAMMAINLINE.scr:37
    do return ctx:exit("") end -- ANSKRAMMAINLINE.scr:39
end

return script
