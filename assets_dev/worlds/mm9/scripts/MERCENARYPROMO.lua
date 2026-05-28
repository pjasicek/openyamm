-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "MERCENARYPROMO.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 12, path = "globals.inc" }

-- Mercenarypromo.scr
-- By Timmy
-- checks to see if player is on promo quest
-- and gives completion key
-- Thorfinn's RudeID is 240
-- Atli's RudeID is 186
-- key 125 = player has got Atli
-- Key 126 = player has taken atli where he belongs
script.labels["OnUse"] = function(ctx)
    -- MERCENARYPROMO.scr:18
    if ctx:hasKey(125) then -- MERCENARYPROMO.scr:22-23
        -- checks to see if player is on quest and has atli in party
        if not ctx:hasKey(126) then -- MERCENARYPROMO.scr:25-26
            -- checks to see if player has already completed quest
            ctx:giveKey(126) -- MERCENARYPROMO.scr:28
            -- gives key that player has put atli where he belongs.
            do return ctx:exit("") end -- MERCENARYPROMO.scr:30
        end -- MERCENARYPROMO.scr:31
    end -- MERCENARYPROMO.scr:32
    do return ctx:exit("") end -- MERCENARYPROMO.scr:33
end

script.labels["Main"] = function(ctx)
    -- MERCENARYPROMO.scr:39
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "OnUse") -- MERCENARYPROMO.scr:43
    do return ctx:exit("") end -- MERCENARYPROMO.scr:46
end

return script
