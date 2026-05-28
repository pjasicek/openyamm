-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "PLOW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

-- Plow.scr
-- By Timmy
-- checks to see if player is on the quest
-- and gives the plow key
-- relevant RudeIDs: 89, 91, 92, 93
-- key 128 = player is on yobboe promo quest
-- Key 130 = player has the plow
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- PLOW.scr:24
    if ctx:hasKey(128) then -- PLOW.scr:28-29
        -- checks to see if player is on the yobboe promo quest
        if not ctx:hasKey(130) then -- PLOW.scr:31-32
            -- checks to see if player has already done this
            ctx:giveKey(130) -- PLOW.scr:34
            ctx:giveItem(371) -- PLOW.scr:35
            ctx:command("getmyhandle", "g_hmyobject") -- PLOW.scr:36
            ctx:command("removeobject", "g_hmyobject") -- PLOW.scr:37
            -- gives plow key.
            do return ctx:exit("") end -- PLOW.scr:39
        end -- PLOW.scr:40
    end -- PLOW.scr:41
    do return ctx:exit("") end -- PLOW.scr:42
end

script.labels["Init"] = function(ctx)
    -- PLOW.scr:46
    if ctx:hasKey(128) then -- PLOW.scr:49-50
        ctx:command("getmyhandle", "g_hobject") -- PLOW.scr:51
        ctx:command("setflag", "g_hobject, visible") -- PLOW.scr:52
        ctx:command("setflag", "g_hobject, solid") -- PLOW.scr:53
        ctx:command("setflag", "g_hobject, gravity") -- PLOW.scr:54
    else -- PLOW.scr:55
        ctx:command("getmyhandle", "g_hobject") -- PLOW.scr:56
        ctx:command("clearflag", "g_hobject, visible") -- PLOW.scr:57
        ctx:command("clearflag", "g_hobject, solid") -- PLOW.scr:58
        ctx:command("clearflag", "g_hobject, gravity") -- PLOW.scr:59
    end -- PLOW.scr:60
    if ctx:hasKey(130) then -- PLOW.scr:62-63
        ctx:command("getmyhandle", "g_hmyobject") -- PLOW.scr:64
        ctx:command("removeobject", "g_hmyobject") -- PLOW.scr:65
        do return ctx:exit("") end -- PLOW.scr:66
    end -- PLOW.scr:67
    do return ctx:exit("") end -- PLOW.scr:68
end

script.labels["Main"] = function(ctx)
    -- PLOW.scr:71
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- PLOW.scr:75
    mm9.gosub(script, ctx, "Init") -- PLOW.scr:77
    do return ctx:exit("") end -- PLOW.scr:78
end

return script
