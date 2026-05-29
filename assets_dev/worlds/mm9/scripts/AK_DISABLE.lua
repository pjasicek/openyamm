-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AK_DISABLE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- Forstenigmainline.scr
-- By Timmy
-- checks to see if the player has disabled ft stening's defenses
script.labels["Award"] = function(ctx)
    -- AK_DISABLE.scr:16
    ctx:state().g_ncounter = 0 -- AK_DISABLE.scr:20
    if ctx:condition("bDrawbridge==TRUE") then -- AK_DISABLE.scr:21
        ctx:state().g_ncounter = (tonumber(ctx:state().g_ncounter) or 0) + 1 -- AK_DISABLE.scr:22
    end -- AK_DISABLE.scr:23
    if ctx:condition("bPortcullis==TRUE") then -- AK_DISABLE.scr:25
        ctx:state().g_ncounter = (tonumber(ctx:state().g_ncounter) or 0) + 1 -- AK_DISABLE.scr:26
    end -- AK_DISABLE.scr:27
    if ctx:condition("g_ncounter!=2") then -- AK_DISABLE.scr:29
        do return ctx:exit("") end -- AK_DISABLE.scr:30
    end -- AK_DISABLE.scr:31
    if ctx:hasKey(372) then -- AK_DISABLE.scr:33-34
        do return ctx:exit("") end -- AK_DISABLE.scr:35
    end -- AK_DISABLE.scr:36
    -- checks to see if player has done this yet
    ctx:hasKey(47, "g_ntemp") -- AK_DISABLE.scr:38
    if ctx:condition("g_ntemp==0") then -- AK_DISABLE.scr:40
        -- checks to see if player is on Fort Stenig Quest
        if ctx:hasKey(44) then -- AK_DISABLE.scr:42-43
            -- gives player finished quest key
            ctx:giveKey("", 47) -- AK_DISABLE.scr:45
            ctx:giveExp(10000) -- AK_DISABLE.scr:46
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 2400, "FALSE", 100) -- AK_DISABLE.scr:47
            do return ctx:exit("") end -- AK_DISABLE.scr:48
        else -- AK_DISABLE.scr:49
            ctx:giveKey(372) -- AK_DISABLE.scr:50
            ctx:giveExp(10000) -- AK_DISABLE.scr:51
            ctx:playSound("sounds\\events\\quest.wav", "DoNothing", 100, 2400, "FALSE", 100) -- AK_DISABLE.scr:52
            do return ctx:exit("") end -- AK_DISABLE.scr:53
        end -- AK_DISABLE.scr:54
    end -- AK_DISABLE.scr:55
    do return ctx:exit("") end -- AK_DISABLE.scr:56
end

script.labels["OnDraw"] = function(ctx)
    -- AK_DISABLE.scr:60
    ctx:state().Drawcounter = (tonumber(ctx:state().Drawcounter) or 0) + 1 -- AK_DISABLE.scr:64
    if ctx:condition("Drawcounter==2") then -- AK_DISABLE.scr:66
        local object = ctx:object("Drawbridgechain") -- AK_DISABLE.scr:67
        object:trigger("DamageOn") -- AK_DISABLE.scr:68
        object:trigger("destroy") -- AK_DISABLE.scr:69
        ctx:object("drawbridge"):trigger("open") -- AK_DISABLE.scr:70-71
        ctx:state().bDrawbridge = true -- AK_DISABLE.scr:72
        mm9.gosub(script, ctx, "Award") -- AK_DISABLE.scr:73
        do return ctx:exit("") end -- AK_DISABLE.scr:74
    end -- AK_DISABLE.scr:75
    do return ctx:exit("") end -- AK_DISABLE.scr:76
end

script.labels["ONPortcullis"] = function(ctx)
    -- AK_DISABLE.scr:80
    ctx:state().bPortcullis = true -- AK_DISABLE.scr:83
    mm9.gosub(script, ctx, "Award") -- AK_DISABLE.scr:84
    do return ctx:exit("") end -- AK_DISABLE.scr:85
end

script.labels["Setup"] = function(ctx)
    -- AK_DISABLE.scr:88
    -- if quest is complete, clears all destructo brushes and
    -- opens portcullis
    local object = ctx:object("Drawbridgechain") -- AK_DISABLE.scr:93
    object:trigger("DamageOn") -- AK_DISABLE.scr:94
    object:trigger("destroy") -- AK_DISABLE.scr:95
    ctx:object("drawbridge"):trigger("open") -- AK_DISABLE.scr:96-97
    ctx:object("DestructableBrush0"):trigger("destroy") -- AK_DISABLE.scr:98-99
    ctx:object("DestructableBrush1"):trigger("destroy") -- AK_DISABLE.scr:100-101
    ctx:object("Drawchainperc"):trigger("off") -- AK_DISABLE.scr:102-103
    ctx:object("Portchainperc"):trigger("off") -- AK_DISABLE.scr:104-105
    local object = ctx:object("Portaclis") -- AK_DISABLE.scr:106
    object:trigger("unlock") -- AK_DISABLE.scr:107
    object:trigger("open") -- AK_DISABLE.scr:108
end

script.labels["Init"] = function(ctx)
    -- AK_DISABLE.scr:111
    if ctx:hasKey(47) then -- AK_DISABLE.scr:114-115
        mm9.gosub(script, ctx, "Setup") -- AK_DISABLE.scr:116
    end -- AK_DISABLE.scr:117
    if ctx:hasKey(372) then -- AK_DISABLE.scr:119-120
        mm9.gosub(script, ctx, "Setup") -- AK_DISABLE.scr:121
    end -- AK_DISABLE.scr:122
    do return ctx:exit("") end -- AK_DISABLE.scr:124
end

script.labels["Main"] = function(ctx)
    -- AK_DISABLE.scr:127
    -- TraceOn ;delete me!!
    -- AddTrigger Use, Onuse
    ctx:addTrigger("Drawbridge", "OnDraw") -- AK_DISABLE.scr:132
    ctx:addTrigger("Portcullis", "ONPortcullis") -- AK_DISABLE.scr:133
    ctx:onEvent("OnPostStartWorld", "Init") -- AK_DISABLE.scr:134
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- AK_DISABLE.scr:135
    ctx:onEvent("OnPostSaveLoad", "Init") -- AK_DISABLE.scr:136
    ctx:wait(1, .1, "Init") -- AK_DISABLE.scr:137
    do return ctx:exit("") end -- AK_DISABLE.scr:138
end

return script
