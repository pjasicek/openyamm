-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FORTSTENINGMAINLINE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Forstenigmainline.scr
-- By Timmy
-- checks to see if the player has disabled ft stening's defenses
script.labels["Onuse"] = function(ctx)
    -- FORTSTENINGMAINLINE.scr:15
    -- NOTE this script just completes the quest right now.
    -- this is the routine where additional functionality should go
    -- checks to see if player has done this yet
    ctx:hasKey(47, "g_ntemp") -- FORTSTENINGMAINLINE.scr:19
    if ctx:condition("g_ntemp==0") then -- FORTSTENINGMAINLINE.scr:21
        -- gives player finished quest key
        ctx:giveKey("", 47) -- FORTSTENINGMAINLINE.scr:23
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- FORTSTENINGMAINLINE.scr:24
        do return ctx:exit("") end -- FORTSTENINGMAINLINE.scr:25
    end -- FORTSTENINGMAINLINE.scr:26
    -- unmatched endif at FORTSTENINGMAINLINE.scr:27
    do return ctx:exit("") end -- FORTSTENINGMAINLINE.scr:28
end

script.labels["Main"] = function(ctx)
    -- FORTSTENINGMAINLINE.scr:34
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onuse") -- FORTSTENINGMAINLINE.scr:38
    do return ctx:exit("") end -- FORTSTENINGMAINLINE.scr:40
end

return script
