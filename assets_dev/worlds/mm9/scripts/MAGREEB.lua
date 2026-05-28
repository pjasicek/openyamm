-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MAGREEB.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "basecrawl.inc" }

-- Magreeb.scr
-- Gives the key for the scholar promo if player
-- is on the quest and find a random Magreeb
-- Timmy
script.labels["OnFoundTarget"] = function(ctx)
    -- MAGREEB.scr:14
    -- p0	- hTarget
    if ctx:hasKey(202) then -- MAGREEB.scr:20-21
        mm9.gosub(script, ctx, "OnFoundTarget") -- MAGREEB.scr:22
        do return ctx:exit("") end -- MAGREEB.scr:23
    end -- MAGREEB.scr:24
    ctx:getParam(0, "g_hObject") -- MAGREEB.scr:27
    ctx:command("isplayer", "g_hobject g_ntemp") -- MAGREEB.scr:29
    if ctx:condition("g_ntemp==TRUE") then -- MAGREEB.scr:30
        if ctx:hasKey(201) then -- MAGREEB.scr:31-32
            ctx:giveKey(202) -- MAGREEB.scr:33
            ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 24000, FALSE, 100") -- MAGREEB.scr:34
        end -- MAGREEB.scr:35
    end -- MAGREEB.scr:36
    mm9.gosub(script, ctx, "OnFoundTarget") -- MAGREEB.scr:38
    do return ctx:exit("") end -- MAGREEB.scr:39
end

script.labels["Main"] = function(ctx)
    -- MAGREEB.scr:43
    -- This routine is automatically run
    -- at script startup...
    mm9.gosub(script, ctx, "BaseCrawlInit") -- MAGREEB.scr:50
    do return ctx:exit("") end -- MAGREEB.scr:52
end

return script
