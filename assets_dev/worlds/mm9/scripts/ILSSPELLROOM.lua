-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSSPELLROOM.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 14, path = "globals.inc" }

-- ILSspellroom.scr
-- Timmy
-- This script Handles the healing room
-- Parameters:
-- Volume Dims Variables
-- Player dim Variables
-- healing variables
-- Heal amount defaults to 10... Change this value in your
-- script if you want....
script.labels["Onclickon"] = function(ctx)
    -- ILSSPELLROOM.scr:56
    if ctx:condition("closed==false") then -- ILSSPELLROOM.scr:60
        do return ctx:exit("") end -- ILSSPELLROOM.scr:61
    end -- ILSSPELLROOM.scr:62
    -- gets the dims of volume brush
    ctx:command("getobjecthandle", "spellinside, g_hobject") -- ILSSPELLROOM.scr:67
    ctx:command("getobjectminmax", "g_hobject, VolumeMinX, VolumeMinY, VolumeMinZ, VolumeMaxX, VolumeMaxY, VolumeMaxZ") -- ILSSPELLROOM.scr:68
    ctx:command("getplayerswithindist", "-1072.0 325.763916 5419.0 512 PlayerIds 8 Playercount") -- ILSSPELLROOM.scr:71
    if ctx:condition("Playercount==0") then -- ILSSPELLROOM.scr:72
        do return ctx:exit("") end -- ILSSPELLROOM.scr:73
    end -- ILSSPELLROOM.scr:74
    ctx:command("set", "loopcounter, 0") -- ILSSPELLROOM.scr:75
end

script.labels["CheckPlayerLoop"] = function(ctx)
    -- ILSSPELLROOM.scr:78
    ctx:command("arrayget", "PlayerIds, loopCounter, g_hobject") -- ILSSPELLROOM.scr:82
    mm9.gosub(script, ctx, "CheckPlayer") -- ILSSPELLROOM.scr:83
    ctx:command("add", "loopcounter, 1") -- ILSSPELLROOM.scr:84
    if ctx:condition("loopcounter<Playercount") then -- ILSSPELLROOM.scr:85
        do return mm9.gotoLabel(script, ctx, "CheckPlayerLoop") end -- ILSSPELLROOM.scr:86
    end -- ILSSPELLROOM.scr:87
    do return ctx:exit("") end -- ILSSPELLROOM.scr:89
end

script.labels["CheckPlayer"] = function(ctx)
    -- ILSSPELLROOM.scr:92
    -- Gets the dims of Player
    ctx:command("getpos", "g_hobject PlayerX, PlayerY, PlayerZ") -- ILSSPELLROOM.scr:100
    if ctx:condition("PlayerX>=VolumeMinX") then -- ILSSPELLROOM.scr:102
        if ctx:condition("PlayerX<=VolumeMaxX") then -- ILSSPELLROOM.scr:103
            if ctx:condition("PlayerY>=VolumeMinY") then -- ILSSPELLROOM.scr:104
                if ctx:condition("PlayerY<=VolumeMaxY") then -- ILSSPELLROOM.scr:105
                    if ctx:condition("PlayerZ>=VolumeMinZ") then -- ILSSPELLROOM.scr:106
                        if ctx:condition("PlayerZ<=VolumeMaxZ") then -- ILSSPELLROOM.scr:107
                            mm9.gosub(script, ctx, "OnHeal") -- ILSSPELLROOM.scr:108
                            -- DEBUGOUT healed Player
                            -- DEBUGOUT loopcounter
                        end -- ILSSPELLROOM.scr:111
                    end -- ILSSPELLROOM.scr:112
                end -- ILSSPELLROOM.scr:113
            end -- ILSSPELLROOM.scr:114
        end -- ILSSPELLROOM.scr:115
    end -- ILSSPELLROOM.scr:116
    do return ctx:exit("") end -- ILSSPELLROOM.scr:118
end

script.labels["OnHeal"] = function(ctx)
    -- ILSSPELLROOM.scr:121
    if ctx:condition("Broken!=true") then -- ILSSPELLROOM.scr:125
        if ctx:condition("counter<=g_nHealCount") then -- ILSSPELLROOM.scr:128
            ctx:command("add", "counter, 1") -- ILSSPELLROOM.scr:130
            mm9.gosub(script, ctx, "HealOnUse") -- ILSSPELLROOM.scr:131
            do return ctx:exit("") end -- ILSSPELLROOM.scr:132
        end -- ILSSPELLROOM.scr:133
        ctx:command("getobjecthandle", "glass1, g_hobject") -- ILSSPELLROOM.scr:136
        ctx:trigger("g_hobject", "destroy") -- ILSSPELLROOM.scr:137
        ctx:command("getobjecthandle", "DestructableBrush9, g_hobject") -- ILSSPELLROOM.scr:138
        ctx:trigger("g_hobject", "destroy") -- ILSSPELLROOM.scr:139
        ctx:command("getobjecthandle", "glassb1, g_hobject") -- ILSSPELLROOM.scr:140
        ctx:trigger("g_hobject", "destroy") -- ILSSPELLROOM.scr:141
        ctx:command("getobjecthandle", "DestructableBrush7, g_hobject") -- ILSSPELLROOM.scr:142
        ctx:trigger("g_hobject", "destroy") -- ILSSPELLROOM.scr:143
        ctx:command("set", "Broken, true") -- ILSSPELLROOM.scr:145
        do return ctx:exit("") end -- ILSSPELLROOM.scr:146
    end -- ILSSPELLROOM.scr:147
    ctx:command("getobjecthandle", "spellinside, g_hobject") -- ILSSPELLROOM.scr:149
    ctx:trigger("g_hobject", "DamageOn") -- ILSSPELLROOM.scr:150
    -- DEBUGOUT broken!!
    do return ctx:exit("") end -- ILSSPELLROOM.scr:152
end

script.labels["Onopen"] = function(ctx)
    -- ILSSPELLROOM.scr:156
    ctx:command("set", "closed, false") -- ILSSPELLROOM.scr:159
    do return ctx:exit("") end -- ILSSPELLROOM.scr:160
end

script.labels["Onclose"] = function(ctx)
    -- ILSSPELLROOM.scr:163
    ctx:command("set", "closed, true") -- ILSSPELLROOM.scr:166
    do return ctx:exit("") end -- ILSSPELLROOM.scr:167
end

script.labels["Onbreak"] = function(ctx)
    -- ILSSPELLROOM.scr:171
    ctx:command("set", "broken, true") -- ILSSPELLROOM.scr:174
    do return ctx:exit("") end -- ILSSPELLROOM.scr:175
end

script.labels["HealOnUse"] = function(ctx)
    -- ILSSPELLROOM.scr:181
    -- See if we should heal the object that triggered
    -- us..
    ctx:command("getplayerid", "g_hObject, g_nPlayerId") -- ILSSPELLROOM.scr:190
    ctx:command("getplayernbr", "g_hObject, g_nPlayerNbr") -- ILSSPELLROOM.scr:191
    if ctx:condition("g_nPlayerNbr==-1") then -- ILSSPELLROOM.scr:193
        -- Not a player!
        do return ctx:exit("FALSE") end -- ILSSPELLROOM.scr:195
    end -- ILSSPELLROOM.scr:196
    ctx:command("arrayget", "g_nPlayerHealedArray, g_nPlayerNbr, g_nTemp") -- ILSSPELLROOM.scr:198
    if ctx:condition("g_nTemp==g_nPlayerId") then -- ILSSPELLROOM.scr:200
        ctx:command("arrayget", "g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp") -- ILSSPELLROOM.scr:201
        if ctx:condition("g_nTemp>=g_nHealCount") then -- ILSSPELLROOM.scr:202
            -- they've already Used this item...
            -- Don't let them do it again...
            do return ctx:exit("FALSE") end -- ILSSPELLROOM.scr:206
        end -- ILSSPELLROOM.scr:207
    else -- ILSSPELLROOM.scr:208
        ctx:command("arrayput", "g_nPlayerHealedCountArray, g_nPlayerNbr, 0") -- ILSSPELLROOM.scr:209
    end -- ILSSPELLROOM.scr:211
    ctx:command("arrayget", "g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp") -- ILSSPELLROOM.scr:213
    ctx:command("add", "g_nTemp, 1") -- ILSSPELLROOM.scr:214
    ctx:command("arrayput", "g_nPlayerHealedCountArray, g_nPlayerNbr, g_nTemp") -- ILSSPELLROOM.scr:215
    ctx:command("arrayput", "g_nPlayerHealedArray, g_nPlayerNbr, g_nPlayerId") -- ILSSPELLROOM.scr:216
    ctx:command("heal", "g_hObject, g_nHealAmt") -- ILSSPELLROOM.scr:218
    -- CHANGE THIS TO HEAL SPELL POINTS!!
    do return ctx:exit("") end -- ILSSPELLROOM.scr:222
end

script.labels["Main"] = function(ctx)
    -- ILSSPELLROOM.scr:224
    -- TRACEON
    ctx:getParam(0, "g_nTemp") -- ILSSPELLROOM.scr:230
    if ctx:condition("g_nTemp!=0") then -- ILSSPELLROOM.scr:232
        ctx:command("set", "g_nHealAmt, g_nTemp") -- ILSSPELLROOM.scr:233
    end -- ILSSPELLROOM.scr:234
    ctx:getParam(1, "g_nTemp") -- ILSSPELLROOM.scr:236
    if ctx:condition("g_nTemp!=0") then -- ILSSPELLROOM.scr:238
        ctx:command("set", "g_nHealCount, g_nTemp") -- ILSSPELLROOM.scr:239
    end -- ILSSPELLROOM.scr:240
    ctx:addTrigger("use", "Onclickon") -- ILSSPELLROOM.scr:244
    ctx:addTrigger("open", "Onopen") -- ILSSPELLROOM.scr:245
    ctx:addTrigger("close", "Onclose") -- ILSSPELLROOM.scr:246
    ctx:addTrigger("break", "Onbreak") -- ILSSPELLROOM.scr:247
    do return ctx:exit("") end -- ILSSPELLROOM.scr:248
end

return script
