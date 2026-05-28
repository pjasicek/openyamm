-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DEFENSE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- defense.scr
-- By Timmy
-- checks to see if the player has killed everything in anskram keep
script.labels["Onuse"] = function(ctx)
    -- DEFENSE.scr:15
    -- NOTE this script just completes the quest right now.
    -- this is the routine where additional functionality should go
    -- checks to see if player has done this yet
    ctx:hasKey(47, "g_ntemp") -- DEFENSE.scr:19
    if ctx:condition("g_ntemp==0") then -- DEFENSE.scr:21
        -- checks to see if player is on kill anskram keep Quest
        ctx:hasKey(44, "keycheck") -- DEFENSE.scr:23
        if ctx:condition("keycheck==1") then -- DEFENSE.scr:24
            -- gives player finished quest key
            ctx:giveKey("", 47) -- DEFENSE.scr:26
            ctx:giveExp(1000) -- DEFENSE.scr:27
            do return ctx:exit("") end -- DEFENSE.scr:28
        end -- DEFENSE.scr:29
    end -- DEFENSE.scr:30
    do return ctx:exit("") end -- DEFENSE.scr:31
end

script.labels["Main"] = function(ctx)
    -- DEFENSE.scr:37
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "Onuse") -- DEFENSE.scr:41
    ctx:addTrigger("disable", "Onuse") -- DEFENSE.scr:42
    do return ctx:exit("") end -- DEFENSE.scr:43
end

return script
