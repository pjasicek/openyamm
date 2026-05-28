-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "HUCKSTER.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Huckster.scr
-- By Timmy
-- handles the strength game the the thing and the gathering.
script.labels["OnUse"] = function(ctx)
    -- HUCKSTER.scr:15
    if ctx:condition("sGame==ArmWrestle") then -- HUCKSTER.scr:18
        ctx:giveKey(1004) -- HUCKSTER.scr:19
        do return ctx:exit("") end -- HUCKSTER.scr:20
    end -- HUCKSTER.scr:21
    do return ctx:exit("") end -- HUCKSTER.scr:23
end

script.labels["OnRude"] = function(ctx)
    -- HUCKSTER.scr:28
    -- looks to see if they want to play a game (key 1001)
    -- and takes their gold and gives them the ticket (key 1002)
    ctx:takeKey(1004) -- HUCKSTER.scr:33
    mm9.gosub(script, ctx, "gamecheck") -- HUCKSTER.scr:36
    mm9.gosub(script, ctx, "prizecheck") -- HUCKSTER.scr:37
    do return ctx:exit("") end -- HUCKSTER.scr:38
end

script.labels["PrizeCheck"] = function(ctx)
    -- HUCKSTER.scr:41
    if ctx:hasKey(1003) then -- HUCKSTER.scr:44-45
        if ctx:condition("sLocation==Guberland") then -- HUCKSTER.scr:46
            mm9.gosub(script, ctx, "Guberland") -- HUCKSTER.scr:47
            do return ctx:exit("") end -- HUCKSTER.scr:48
        else -- HUCKSTER.scr:49
            ctx:giveItem(253) -- HUCKSTER.scr:50
            ctx:takeKey(1003) -- HUCKSTER.scr:51
            do return ctx:exit("") end -- HUCKSTER.scr:52
        end -- HUCKSTER.scr:53
    end -- HUCKSTER.scr:54
    do return ctx:exit("") end -- HUCKSTER.scr:55
end

script.labels["Guberland"] = function(ctx)
    -- HUCKSTER.scr:58
    -- gives guberland prizes
    ctx:command("getrandomint", "1, 6 g_ntemp") -- HUCKSTER.scr:62
    ctx:takeKey(1003) -- HUCKSTER.scr:63
    if ctx:condition("g_ntemp==1") then -- HUCKSTER.scr:65
        ctx:giveItem(362) -- HUCKSTER.scr:66
        do return ctx:exit("") end -- HUCKSTER.scr:67
    end -- HUCKSTER.scr:68
    if ctx:condition("g_ntemp==2") then -- HUCKSTER.scr:70
        ctx:giveItem(363) -- HUCKSTER.scr:71
        do return ctx:exit("") end -- HUCKSTER.scr:72
    end -- HUCKSTER.scr:73
    if ctx:condition("g_ntemp==3") then -- HUCKSTER.scr:75
        ctx:giveItem(364) -- HUCKSTER.scr:76
        do return ctx:exit("") end -- HUCKSTER.scr:77
    end -- HUCKSTER.scr:78
    if ctx:condition("g_ntemp==4") then -- HUCKSTER.scr:80
        ctx:giveItem(365) -- HUCKSTER.scr:81
        do return ctx:exit("") end -- HUCKSTER.scr:82
    end -- HUCKSTER.scr:83
    if ctx:condition("g_ntemp==5") then -- HUCKSTER.scr:85
        ctx:giveItem(366) -- HUCKSTER.scr:86
        do return ctx:exit("") end -- HUCKSTER.scr:87
    end -- HUCKSTER.scr:88
    if ctx:condition("g_ntemp==6") then -- HUCKSTER.scr:89
        ctx:giveItem(367) -- HUCKSTER.scr:90
        do return ctx:exit("") end -- HUCKSTER.scr:91
    end -- HUCKSTER.scr:92
    do return ctx:exit("") end -- HUCKSTER.scr:94
end

script.labels["Gamecheck"] = function(ctx)
    -- HUCKSTER.scr:97
    if ctx:hasKey(1001) then -- HUCKSTER.scr:100-101
        ctx:command("hasgold", "5 g_ntemp") -- HUCKSTER.scr:102
        if ctx:condition("g_ntemp==TRUE") then -- HUCKSTER.scr:103
            ctx:takeKey(1001) -- HUCKSTER.scr:104
            ctx:command("takegold", "5") -- HUCKSTER.scr:105
            ctx:giveKey(1002) -- HUCKSTER.scr:106
            ctx:giveItem(557) -- HUCKSTER.scr:107
            do return ctx:exit("") end -- HUCKSTER.scr:108
        end -- HUCKSTER.scr:109
    end -- HUCKSTER.scr:110
    do return ctx:exit("") end -- HUCKSTER.scr:111
end

script.labels["Main"] = function(ctx)
    -- HUCKSTER.scr:114
    -- TraceOn ;delete me!!
    ctx:addTrigger("Use", "OnUse") -- HUCKSTER.scr:118
    ctx:onRudeExit("OnRude", script.labels["OnRude"]) -- HUCKSTER.scr:119
    ctx:getParam(0, "sLocation") -- HUCKSTER.scr:120
    ctx:getParam(1, "sGame") -- HUCKSTER.scr:121
    do return ctx:exit("") end -- HUCKSTER.scr:122
end

return script
