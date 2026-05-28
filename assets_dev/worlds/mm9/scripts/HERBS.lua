-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HERBS.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

-- herbs.scr
-- By Timmy
-- checks to see if player is on the quest
-- and gives the herbs key
-- relevant RudeIDs: 89, 91, 92, 93
-- key 128 = player is on yobboe promo quest
-- Key 131 = player has the plow
-- flag variables
script.labels["OnUse"] = function(ctx)
    -- HERBS.scr:24
    if ctx:hasKey(128) then -- HERBS.scr:28-29
        -- checks to see if player is on the yobboe promo quest
        if not ctx:hasKey(131) then -- HERBS.scr:31-32
            -- checks to see if player has already done this
            ctx:giveKey(131) -- HERBS.scr:34
            ctx:giveItem(372) -- HERBS.scr:35
            ctx:command("getmyhandle", "g_hmyobject") -- HERBS.scr:36
            ctx:command("removeobject", "g_hmyobject") -- HERBS.scr:37
            -- gives herbs key.
            do return ctx:exit("") end -- HERBS.scr:39
        end -- HERBS.scr:40
    end -- HERBS.scr:41
    do return ctx:exit("") end -- HERBS.scr:42
end

script.labels["Init"] = function(ctx)
    -- HERBS.scr:46
    if ctx:hasKey(128) then -- HERBS.scr:49-50
        ctx:command("getmyhandle", "g_hobject") -- HERBS.scr:51
        ctx:command("setflag", "g_hobject, visible") -- HERBS.scr:52
        ctx:command("setflag", "g_hobject, solid") -- HERBS.scr:53
        ctx:command("setflag", "g_hobject, gravity") -- HERBS.scr:54
    else -- HERBS.scr:55
        ctx:command("getmyhandle", "g_hobject") -- HERBS.scr:56
        ctx:command("clearflag", "g_hobject, visible") -- HERBS.scr:57
        ctx:command("clearflag", "g_hobject, solid") -- HERBS.scr:58
        ctx:command("clearflag", "g_hobject, gravity") -- HERBS.scr:59
    end -- HERBS.scr:60
    if ctx:hasKey(131) then -- HERBS.scr:63-64
        ctx:command("getmyhandle", "g_hmyobject") -- HERBS.scr:65
        ctx:command("removeobject", "g_hmyobject") -- HERBS.scr:66
        do return ctx:exit("") end -- HERBS.scr:67
    end -- HERBS.scr:68
    do return ctx:exit("") end -- HERBS.scr:69
end

script.labels["Main"] = function(ctx)
    -- HERBS.scr:72
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Use", "Onuse") -- HERBS.scr:76
    mm9.gosub(script, ctx, "Init") -- HERBS.scr:77
    do return ctx:exit("") end -- HERBS.scr:79
end

return script
