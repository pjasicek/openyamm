-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "YOBBOE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 13, path = "globals.inc" }

-- yobboe.scr
-- By Timmy
-- checks to see if player has killed all the yobboes
-- and gives completion key and reward.
-- relevant RudeIDs: 89, 91, 92, 93
-- key 128 = player is on yobboe promo quest
-- Key 129 = player has killed all the yobboes
script.labels["OnUse"] = function(ctx)
    -- YOBBOE.scr:19
    if ctx:hasKey(128) then -- YOBBOE.scr:23-24
        -- checks to see if player is on the yobboe promo quest
        if not ctx:hasKey(129) then -- YOBBOE.scr:26-27
            -- checks to see if player has already completed quest
            ctx:giveKey(129) -- YOBBOE.scr:29
            -- gives key and reward.
            do return ctx:exit("") end -- YOBBOE.scr:31
        end -- YOBBOE.scr:32
    end -- YOBBOE.scr:33
    do return ctx:exit("") end -- YOBBOE.scr:34
end

script.labels["Main"] = function(ctx)
    -- YOBBOE.scr:40
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- YOBBOE.scr:44
    do return ctx:exit("") end -- YOBBOE.scr:47
end

return script
