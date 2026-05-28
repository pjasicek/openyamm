-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YANMIR.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Yanmir.scr
-- By Timmy
-- checks to see if the player has killed everything in anskram keep
script.labels["GiveEeps"] = function(ctx)
    -- YANMIR.scr:15
    -- NOTE this script just completes the quest right now.
    -- this is the routine where additional functionality should go
    -- checks to see if player has done this yet
    ctx:hasKey(69, "g_ntemp") -- YANMIR.scr:19
    if ctx:condition("g_ntemp==0") then -- YANMIR.scr:21
        -- checks to see if player is on kill anskram keep Quest
        ctx:hasKey(68, "keycheck") -- YANMIR.scr:23
        if ctx:condition("keycheck==1") then -- YANMIR.scr:24
            -- gives player finished quest key
            ctx:giveKey("", 69) -- YANMIR.scr:26
            ctx:giveExp(8000) -- YANMIR.scr:27
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- YANMIR.scr:28
            do return ctx:exit("") end -- YANMIR.scr:29
        end -- YANMIR.scr:30
    end -- YANMIR.scr:31
    -- checks to see if player is on kill anskram keep Quest
    ctx:hasKey(173, "keycheck") -- YANMIR.scr:33
    if ctx:condition("keycheck==0") then -- YANMIR.scr:34
        -- gives player finished quest key
        ctx:giveKey("", 173) -- YANMIR.scr:36
        ctx:giveExp(8000) -- YANMIR.scr:37
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- YANMIR.scr:38
        do return ctx:exit("") end -- YANMIR.scr:39
    end -- YANMIR.scr:40
    do return ctx:exit("") end -- YANMIR.scr:41
end

script.labels["Main"] = function(ctx)
    -- YANMIR.scr:47
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "DoNothing") -- YANMIR.scr:51
    ctx:addTrigger("Trigger", "DoNothing") -- YANMIR.scr:52
    do return ctx:exit("") end -- YANMIR.scr:53
end

return script
