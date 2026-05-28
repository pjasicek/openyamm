-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CAPSTONE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 18, path = "globals.inc" }

-- Capstone.scr
-- By Timmy
-- gives the player the Capstone of Order
-- and the related key
-- Igrid's RudeID is 338
-- capstone is item 396
-- NOTE:  The final quest has changed, so you don't need to get
-- the capstone a second time to lure Njam into tomb
-- edited by Bones 6/12/02, 5/1/03
-- Patch 1.3 -- Capstone won't disappear if not picked up in Guberland.
-- Pentagram Door perception brush removed if bolt broken.
-- flag variables
script.labels["Onuse"] = function(ctx)
    -- CAPSTONE.scr:30
    mm9.gosub(script, ctx, "firsttime") -- CAPSTONE.scr:33
    do return ctx:exit("") end -- CAPSTONE.scr:35
end

script.labels["firsttime"] = function(ctx)
    -- CAPSTONE.scr:37
    if not ctx:hasKey(98) then -- CAPSTONE.scr:40-41
        ctx:giveItem(396) -- CAPSTONE.scr:42
        ctx:command("getmyhandle", "g_hobject") -- CAPSTONE.scr:43
        ctx:command("removeobject", "g_hobject") -- CAPSTONE.scr:44
        do return ctx:exit("") end -- CAPSTONE.scr:45
    end -- CAPSTONE.scr:46
    -- checks to see if player has picked up the capstone already
    ctx:hasKey(188, "keycheck") -- CAPSTONE.scr:48
    if ctx:condition("keycheck==0") then -- CAPSTONE.scr:49
        -- gives player finished quest key
        ctx:giveKey("", 188) -- CAPSTONE.scr:51
        -- this is where the capstone should be removed and added to inventory
        ctx:giveItem(396) -- CAPSTONE.scr:56
        ctx:giveExp(146000) -- CAPSTONE.scr:57
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- CAPSTONE.scr:58
        ctx:command("getmyhandle", "g_hobject") -- CAPSTONE.scr:59
        ctx:command("removeobject", "g_hobject") -- CAPSTONE.scr:60
        do return ctx:exit("") end -- CAPSTONE.scr:61
    end -- CAPSTONE.scr:62
    do return ctx:exit("") end -- CAPSTONE.scr:63
end

script.labels["OnPlace"] = function(ctx)
    -- CAPSTONE.scr:68
    if not ctx:hasKey(99) then -- CAPSTONE.scr:71-72
        ctx:giveKey(99) -- CAPSTONE.scr:73
        ctx:giveExp(154000) -- CAPSTONE.scr:74
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- CAPSTONE.scr:75
        ctx:command("setflag", "g_hobject, visible") -- CAPSTONE.scr:76
        -- setflag g_hobject, solid
        -- setflag g_hobject, gravity
        ctx:command("getobjecthandle", "writ g_hobject") -- CAPSTONE.scr:79
        ctx:trigger("g_hobject", "init") -- CAPSTONE.scr:80
        ctx:takeItem(396) -- CAPSTONE.scr:81
        do return ctx:exit("") end -- CAPSTONE.scr:82
    end -- CAPSTONE.scr:83
    do return ctx:exit("") end -- CAPSTONE.scr:84
end

script.labels["placed"] = function(ctx)
    -- CAPSTONE.scr:89
    if ctx:hasKey(99) then -- CAPSTONE.scr:92-93
        ctx:command("getmyhandle", "g_hobject") -- CAPSTONE.scr:94
        ctx:command("setflag", "g_hobject, visible") -- CAPSTONE.scr:95
        -- setflag g_hobject, solid
        -- setflag g_hobject, gravity
        do return ctx:exit("") end -- CAPSTONE.scr:98
    else -- CAPSTONE.scr:99
        ctx:command("getmyhandle", "g_hobject") -- CAPSTONE.scr:100
        ctx:command("clearflag", "g_hobject, visible") -- CAPSTONE.scr:101
        -- clearflag g_hobject, solid
        -- clearflag g_hobject, gravity
        do return ctx:exit("") end -- CAPSTONE.scr:104
    end -- CAPSTONE.scr:105
end

script.labels["Init"] = function(ctx)
    -- CAPSTONE.scr:109
    if ctx:condition("g_stemp==guberland") then -- CAPSTONE.scr:112
        ctx:hasKey(188, "keycheck") -- CAPSTONE.scr:113
        if ctx:condition("keycheck==1") then -- CAPSTONE.scr:114
            ctx:command("getmyhandle", "g_hobject") -- CAPSTONE.scr:115
            ctx:command("removeobject", "g_hobject") -- CAPSTONE.scr:116
            ctx:command("exitscript", "") -- CAPSTONE.scr:117
        end -- CAPSTONE.scr:118
        do return ctx:exit("") end -- CAPSTONE.scr:119
    end -- CAPSTONE.scr:120
    if ctx:condition("g_stemp==verhoffin") then -- CAPSTONE.scr:122
        mm9.gosub(script, ctx, "placed") -- CAPSTONE.scr:123
        do return ctx:exit("") end -- CAPSTONE.scr:125
    end -- CAPSTONE.scr:126
end

script.labels["Main"] = function(ctx)
    -- CAPSTONE.scr:129
    -- TraceOn ;DELETE ME!!
    -- AddTrigger Use, Onuse
    ctx:addTrigger("place", "OnPlace") -- CAPSTONE.scr:135
    ctx:getParam(0, "g_stemp") -- CAPSTONE.scr:136
    ctx:command("onpoststartworld", "Init") -- CAPSTONE.scr:137
    ctx:command("onpostminisaveload", "Init") -- CAPSTONE.scr:138
    ctx:command("onpostsaveload", "Init") -- CAPSTONE.scr:139
    ctx:command("wait", "1 1 Init") -- CAPSTONE.scr:140
    do return ctx:exit("") end -- CAPSTONE.scr:143
end

script.labels["placed"] = function(ctx)
    -- CAPSTONE.scr:147
    -- overloaded -- Bones
    ctx:command("getobjecthandle", "DestructableBrush12 g_hobject") -- CAPSTONE.scr:151
    if ctx:condition("g_hobject == NULL") then -- CAPSTONE.scr:152
        ctx:command("getobjecthandle", "PerceptionBrush0 g_hobject") -- CAPSTONE.scr:153
        if ctx:condition("g_hobject != NULL") then -- CAPSTONE.scr:154
            ctx:command("removeobject", "g_hobject") -- CAPSTONE.scr:155
        end -- CAPSTONE.scr:156
        ctx:command("getobjecthandle", "PrisonDoor2 g_hobject2") -- CAPSTONE.scr:158
        ctx:command("setstat", "g_hobject2 Locked FALSE") -- CAPSTONE.scr:159
    end -- CAPSTONE.scr:162
    do return mm9.gotoLabel(script, ctx, "placed") end -- CAPSTONE.scr:164
end

return script
