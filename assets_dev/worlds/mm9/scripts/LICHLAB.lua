-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHLAB.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- LichLab.scr
-- By Timmy
-- gives the player the Lich Promo
-- and the related key
-- Lich Instructions is item 245
script.labels["OnUse"] = function(ctx)
    -- LICHLAB.scr:14
    if not ctx:hasKey(297) then -- LICHLAB.scr:17-18
        if ctx:hasKey(296) then -- LICHLAB.scr:19-20
            ctx:giveExp(10000) -- LICHLAB.scr:21
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 240, "FALSE", 100) -- LICHLAB.scr:22
            -- give promo here
            ctx:giveKey(297) -- LICHLAB.scr:24
            do return ctx:exit("") end -- LICHLAB.scr:25
        end -- LICHLAB.scr:26
    end -- LICHLAB.scr:27
    do return ctx:exit("") end -- LICHLAB.scr:28
end

-- note:  this just completes the quest right now.
-- the actual lich procedure still needs to be implemented
script.labels["Main"] = function(ctx)
    -- LICHLAB.scr:34
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- LICHLAB.scr:38
    do return ctx:exit("") end -- LICHLAB.scr:41
end

return script
