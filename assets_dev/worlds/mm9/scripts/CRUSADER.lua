-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CRUSADER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "globals.inc" }

-- crusader.scr
-- By Timmy
-- checks to see if player has completed the quest
-- and gives the reward
-- relevant RudeIDs: 89, 91, 92, 93
-- key 128 = player is on yobboe promo quest
-- Key 131 = player has the plow
-- key 136 = player is done and ready for reward
-- key 137 = playeer is promoted
script.labels["OnExit"] = function(ctx)
    -- CRUSADER.scr:21
    if ctx:hasKey(136) then -- CRUSADER.scr:25-26
        -- checks to see if player has completed quest
        if not ctx:hasKey(137) then -- CRUSADER.scr:28-29
            -- checks to see if player has already completed quest and got reward
            ctx:giveKey(137) -- CRUSADER.scr:31
            ctx:giveGold(2000) -- CRUSADER.scr:32
            ctx:giveExp(8000) -- CRUSADER.scr:33
            -- GIVE PROMO HERE
            -- gives key and reward.
            do return ctx:exit("") end -- CRUSADER.scr:36
        end -- CRUSADER.scr:37
    end -- CRUSADER.scr:38
    do return ctx:exit("") end -- CRUSADER.scr:39
end

script.labels["Main"] = function(ctx)
    -- CRUSADER.scr:45
    -- TraceOn ;DELETE ME!!
    ctx:onRudeExit("OnExit", script.labels["OnExit"]) -- CRUSADER.scr:49
    do return ctx:exit("") end -- CRUSADER.scr:52
end

return script
