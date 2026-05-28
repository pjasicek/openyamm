-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSHEALERROOM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 33, path = "globals.inc" }

-- ILShealerroom.scr
-- Timmy
-- This script Handles the lich promo
-- Parameters:
-- promo variables
-- Volume Dims Variables
-- Player dim Variables
script.labels["Onclickon"] = function(ctx)
    -- ILSHEALERROOM.scr:61
    if ctx:condition("nWorking==FALSE") then -- ILSHEALERROOM.scr:64
        do return ctx:exit("") end -- ILSHEALERROOM.scr:65
    end -- ILSHEALERROOM.scr:66
    if ctx:condition("closed==false") then -- ILSHEALERROOM.scr:68
        do return ctx:exit("") end -- ILSHEALERROOM.scr:69
    end -- ILSHEALERROOM.scr:70
    -- gets the dims of volume brush
    ctx:command("getobjecthandle", "PromoVol1 g_hobject") -- ILSHEALERROOM.scr:75
    ctx:command("getobjectminmax", "g_hobject, VolumeMinX, VolumeMinY, VolumeMinZ, VolumeMaxX, VolumeMaxY, VolumeMaxZ") -- ILSHEALERROOM.scr:76
    mm9.gosub(script, ctx, "CheckPlayer") -- ILSHEALERROOM.scr:77
    ctx:command("wait", "1 2 Open") -- ILSHEALERROOM.scr:79
    ctx:command("getobjecthandle", "Lightning0 g_hobject") -- ILSHEALERROOM.scr:80
    ctx:trigger("g_hobject", "Off") -- ILSHEALERROOM.scr:81
    do return ctx:exit("") end -- ILSHEALERROOM.scr:83
end

script.labels["CheckPlayer"] = function(ctx)
    -- ILSHEALERROOM.scr:88
    -- Gets the dims of Player
    ctx:command("getplayerhandle", "g_hPlayer") -- ILSHEALERROOM.scr:95
    ctx:command("getpos", "g_hPlayer PlayerX, PlayerY, PlayerZ") -- ILSHEALERROOM.scr:96
    if ctx:condition("PlayerX>=VolumeMinX") then -- ILSHEALERROOM.scr:98
        if ctx:condition("PlayerX<=VolumeMaxX") then -- ILSHEALERROOM.scr:99
            if ctx:condition("PlayerY>=VolumeMinY") then -- ILSHEALERROOM.scr:100
                if ctx:condition("PlayerY<=VolumeMaxY") then -- ILSHEALERROOM.scr:101
                    if ctx:condition("PlayerZ>=VolumeMinZ") then -- ILSHEALERROOM.scr:102
                        if ctx:condition("Playerz<=VolumeMaxZ") then -- ILSHEALERROOM.scr:103
                            mm9.gosub(script, ctx, "OnPromo") -- ILSHEALERROOM.scr:104
                            -- DEBUGOUT healed Player
                            -- DEBUGOUT loopcounter
                        end -- ILSHEALERROOM.scr:107
                    end -- ILSHEALERROOM.scr:108
                end -- ILSHEALERROOM.scr:109
            end -- ILSHEALERROOM.scr:110
        end -- ILSHEALERROOM.scr:111
    end -- ILSHEALERROOM.scr:112
    do return ctx:exit("") end -- ILSHEALERROOM.scr:114
end

script.labels["OnPromo"] = function(ctx)
    -- ILSHEALERROOM.scr:117
    if not ctx:hasKey(299) then -- ILSHEALERROOM.scr:119-120
        ctx:giveExp(63000) -- ILSHEALERROOM.scr:121
        ctx:command("playsound", "sounds\\events\\quest.wav, DoNothing, 100, 240, FALSE, 100") -- ILSHEALERROOM.scr:122
    end -- ILSHEALERROOM.scr:123
    if ctx:hasKey(433) then -- ILSHEALERROOM.scr:125-126
        ctx:command("givepromo", "Lich Char1") -- ILSHEALERROOM.scr:127
        ctx:takeKey(433) -- ILSHEALERROOM.scr:128
        ctx:giveKey(299) -- ILSHEALERROOM.scr:129
    end -- ILSHEALERROOM.scr:130
    if ctx:hasKey(434) then -- ILSHEALERROOM.scr:132-133
        ctx:command("givepromo", "Lich Char2") -- ILSHEALERROOM.scr:134
        ctx:takeKey(434) -- ILSHEALERROOM.scr:135
        ctx:giveKey(299) -- ILSHEALERROOM.scr:136
    end -- ILSHEALERROOM.scr:137
    if ctx:hasKey(435) then -- ILSHEALERROOM.scr:139-140
        ctx:command("givepromo", "Lich Char3") -- ILSHEALERROOM.scr:141
        ctx:takeKey(435) -- ILSHEALERROOM.scr:142
        ctx:giveKey(299) -- ILSHEALERROOM.scr:143
    end -- ILSHEALERROOM.scr:144
    if ctx:hasKey(436) then -- ILSHEALERROOM.scr:146-147
        ctx:command("givepromo", "Lich Char4") -- ILSHEALERROOM.scr:148
        ctx:takeKey(436) -- ILSHEALERROOM.scr:149
        ctx:giveKey(299) -- ILSHEALERROOM.scr:150
    end -- ILSHEALERROOM.scr:151
    do return ctx:exit("") end -- ILSHEALERROOM.scr:154
    do return ctx:exit("") end -- ILSHEALERROOM.scr:156
end

script.labels["Open"] = function(ctx)
    -- ILSHEALERROOM.scr:159
    ctx:command("set", "closed, false") -- ILSHEALERROOM.scr:162
    ctx:command("getobjecthandle", "Enginedoor1 g_hobject") -- ILSHEALERROOM.scr:163
    ctx:trigger("g_hobject", "use") -- ILSHEALERROOM.scr:164
    do return ctx:exit("") end -- ILSHEALERROOM.scr:165
end

script.labels["Onopen"] = function(ctx)
    -- ILSHEALERROOM.scr:168
    ctx:command("set", "closed, false") -- ILSHEALERROOM.scr:171
    do return ctx:exit("") end -- ILSHEALERROOM.scr:172
end

script.labels["Onclose"] = function(ctx)
    -- ILSHEALERROOM.scr:175
    ctx:command("set", "closed, true") -- ILSHEALERROOM.scr:178
    ctx:command("wait", "1 3 OnClickOn") -- ILSHEALERROOM.scr:179
    do return ctx:exit("") end -- ILSHEALERROOM.scr:180
end

script.labels["OnFix"] = function(ctx)
    -- ILSHEALERROOM.scr:184
    ctx:command("set", "nWorking, true") -- ILSHEALERROOM.scr:187
    ctx:command("wait", "1 3, Lightning") -- ILSHEALERROOM.scr:188
    do return ctx:exit("") end -- ILSHEALERROOM.scr:189
end

script.labels["Lightning"] = function(ctx)
    -- ILSHEALERROOM.scr:192
    -- getobjecthandle Lightning0 g_hobject
    -- trigger g_hobject ON
    do return ctx:exit("") end -- ILSHEALERROOM.scr:197
end

script.labels["Main"] = function(ctx)
    -- ILSHEALERROOM.scr:200
    -- TRACEON
    -- Addtrigger use, Onclickon
    ctx:addTrigger("open", "Onopen") -- ILSHEALERROOM.scr:206
    ctx:addTrigger("close", "Onclose") -- ILSHEALERROOM.scr:207
    ctx:addTrigger("Fix", "OnFix") -- ILSHEALERROOM.scr:208
    do return ctx:exit("") end -- ILSHEALERROOM.scr:210
end

return script
