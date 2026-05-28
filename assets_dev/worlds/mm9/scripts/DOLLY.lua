-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DOLLY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

-- dolly.scr
-- By Timmy
-- checks to see if player is on the quest
-- and gives the dolly key
-- relevant RudeIDs: 89, 91, 92, 93
-- key 128 = player is on yobboe promo quest
-- Key 132 = player has the plow
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- DOLLY.scr:24
    if ctx:hasKey(128) then -- DOLLY.scr:28-29
        -- checks to see if player is on the yobboe promo quest
        if not ctx:hasKey(132) then -- DOLLY.scr:31-32
            -- checks to see if player has already done this
            ctx:giveKey(132) -- DOLLY.scr:34
            ctx:giveItem(370) -- DOLLY.scr:35
            ctx:command("getmyhandle", "g_hmyobject") -- DOLLY.scr:36
            ctx:command("removeobject", "g_hmyobject") -- DOLLY.scr:37
            -- gives dolly key.
            do return ctx:exit("") end -- DOLLY.scr:39
        end -- DOLLY.scr:40
    end -- DOLLY.scr:41
    do return ctx:exit("") end -- DOLLY.scr:42
end

script.labels["Init"] = function(ctx)
    -- DOLLY.scr:46
    if ctx:hasKey(128) then -- DOLLY.scr:49-50
        ctx:command("getmyhandle", "g_hobject") -- DOLLY.scr:51
        ctx:command("setflag", "g_hobject, visible") -- DOLLY.scr:52
        ctx:command("setflag", "g_hobject, solid") -- DOLLY.scr:53
        ctx:command("setflag", "g_hobject, gravity") -- DOLLY.scr:54
    else -- DOLLY.scr:55
        ctx:command("getmyhandle", "g_hobject") -- DOLLY.scr:56
        ctx:command("clearflag", "g_hobject, visible") -- DOLLY.scr:57
        ctx:command("clearflag", "g_hobject, solid") -- DOLLY.scr:58
        ctx:command("clearflag", "g_hobject, gravity") -- DOLLY.scr:59
    end -- DOLLY.scr:60
    if ctx:hasKey(132) then -- DOLLY.scr:62-63
        ctx:command("getmyhandle", "g_hmyobject") -- DOLLY.scr:64
        ctx:command("removeobject", "g_hmyobject") -- DOLLY.scr:65
        do return ctx:exit("") end -- DOLLY.scr:66
    end -- DOLLY.scr:67
    do return ctx:exit("") end -- DOLLY.scr:68
end

script.labels["Main"] = function(ctx)
    -- DOLLY.scr:71
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- DOLLY.scr:75
    mm9.gosub(script, ctx, "Init") -- DOLLY.scr:76
    do return ctx:exit("") end -- DOLLY.scr:78
end

return script
