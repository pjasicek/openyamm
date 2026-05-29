-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FORADWORLD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Foradworld.scr
-- 1/12/02
-- timmy
-- Gives player location key for Forad Darre
-- Parameters
-- P0 The object name of the target
-- P1 the trigger message to send
script.labels["TakeKey"] = function(ctx)
    -- FORADWORLD.scr:23
    ctx:takeKey(1024) -- FORADWORLD.scr:26
    ctx:takeKey(1025) -- FORADWORLD.scr:27
    ctx:takeKey(1026) -- FORADWORLD.scr:28
    ctx:takeKey(1027) -- FORADWORLD.scr:29
    ctx:takeKey(1028) -- FORADWORLD.scr:30
    ctx:takeKey(1029) -- FORADWORLD.scr:31
    ctx:takeKey(1030) -- FORADWORLD.scr:32
    ctx:takeKey(1031) -- FORADWORLD.scr:33
    ctx:takeKey(1032) -- FORADWORLD.scr:34
    ctx:takeKey(1033) -- FORADWORLD.scr:35
    do return ctx:exit("") end -- FORADWORLD.scr:36
end

script.labels["Init"] = function(ctx)
    -- FORADWORLD.scr:39
    ctx:takeKey(1024) -- FORADWORLD.scr:42
    ctx:takeKey(1025) -- FORADWORLD.scr:43
    ctx:takeKey(1026) -- FORADWORLD.scr:44
    ctx:takeKey(1027) -- FORADWORLD.scr:45
    ctx:takeKey(1028) -- FORADWORLD.scr:46
    ctx:takeKey(1029) -- FORADWORLD.scr:47
    ctx:takeKey(1030) -- FORADWORLD.scr:48
    ctx:takeKey(1031) -- FORADWORLD.scr:49
    ctx:takeKey(1032) -- FORADWORLD.scr:50
    ctx:takeKey(1033) -- FORADWORLD.scr:51
    if ctx:condition("sWorld==IsleOfAshes") then -- FORADWORLD.scr:53
        ctx:giveKey(1024) -- FORADWORLD.scr:54
        do return ctx:exit("") end -- FORADWORLD.scr:55
    end -- FORADWORLD.scr:56
    if ctx:condition("sWorld==Thjorgard") then -- FORADWORLD.scr:58
        ctx:giveKey(1025) -- FORADWORLD.scr:59
        do return ctx:exit("") end -- FORADWORLD.scr:60
    end -- FORADWORLD.scr:61
    if ctx:condition("sWorld==Sturmford") then -- FORADWORLD.scr:63
        ctx:giveKey(1026) -- FORADWORLD.scr:64
        do return ctx:exit("") end -- FORADWORLD.scr:65
    end -- FORADWORLD.scr:66
    if ctx:condition("sWorld==Drangheim") then -- FORADWORLD.scr:68
        ctx:giveKey(1027) -- FORADWORLD.scr:69
        do return ctx:exit("") end -- FORADWORLD.scr:70
    end -- FORADWORLD.scr:71
    if ctx:condition("sWorld==Guberland") then -- FORADWORLD.scr:73
        ctx:giveKey(1028) -- FORADWORLD.scr:74
        do return ctx:exit("") end -- FORADWORLD.scr:75
    end -- FORADWORLD.scr:76
    if ctx:condition("sWorld==Frosgard") then -- FORADWORLD.scr:78
        ctx:giveKey(1029) -- FORADWORLD.scr:79
        do return ctx:exit("") end -- FORADWORLD.scr:80
    end -- FORADWORLD.scr:81
    if ctx:condition("sWorld==Thronheim") then -- FORADWORLD.scr:83
        ctx:giveKey(1030) -- FORADWORLD.scr:84
        do return ctx:exit("") end -- FORADWORLD.scr:85
    end -- FORADWORLD.scr:86
    if ctx:condition("sWorld==Lindisfarne") then -- FORADWORLD.scr:88
        ctx:giveKey(1031) -- FORADWORLD.scr:89
        do return ctx:exit("") end -- FORADWORLD.scr:90
    end -- FORADWORLD.scr:91
    if ctx:condition("sWorld==Yorwick") then -- FORADWORLD.scr:93
        ctx:giveKey(1032) -- FORADWORLD.scr:94
        do return ctx:exit("") end -- FORADWORLD.scr:95
    end -- FORADWORLD.scr:96
    ctx:giveKey(1033) -- FORADWORLD.scr:98
    -- GetWorldName sWorld
    -- debugout sWorld
    do return ctx:exit("") end -- FORADWORLD.scr:103
end

script.labels["Close"] = function(ctx)
    -- FORADWORLD.scr:106
    -- for closing shops
    ctx:giveKey(5017) -- FORADWORLD.scr:110
    do return ctx:exit("") end -- FORADWORLD.scr:111
end

script.labels["Open"] = function(ctx)
    -- FORADWORLD.scr:114
    -- for opening shops
    ctx:takeKey(5017) -- FORADWORLD.scr:118
    do return ctx:exit("") end -- FORADWORLD.scr:119
end

script.labels["Main"] = function(ctx)
    -- FORADWORLD.scr:123
    -- traceon
    ctx:getParam(0, "sWorld") -- FORADWORLD.scr:128
    ctx:atTime(20, 0, "Close", "Close") -- FORADWORLD.scr:129
    ctx:atTime(6, 0, "Open", "Open") -- FORADWORLD.scr:130
    ctx:wait(1, 1, "Init") -- FORADWORLD.scr:131
    ctx:onEvent("OnPostStartWorld", "Init") -- FORADWORLD.scr:132
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- FORADWORLD.scr:133
    ctx:onEvent("OnPostSaveLoad", "Init") -- FORADWORLD.scr:134
    ctx:onEvent("OnWorldSwitch", "TakeKey") -- FORADWORLD.scr:135
    do return ctx:exit("") end -- FORADWORLD.scr:136
end

return script
