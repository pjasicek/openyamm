-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "COLLOIDALGENIE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }

-- BaseGlobals.inc
-- by SJR
-- 11-12-01
-- Purpose:be a genie
script.labels["Main"] = function(ctx)
    -- COLLOIDALGENIE.scr:24
    ctx:getParam(0, "sAppearName") -- COLLOIDALGENIE.scr:26
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- COLLOIDALGENIE.scr:28
    mm9.gosub(script, ctx, "InitColloidalGenie") -- COLLOIDALGENIE.scr:30
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:32
end

script.labels["CacheFiles"] = function(ctx)
    -- COLLOIDALGENIE.scr:35
    ctx:cacheClientFx("SPELL_MIST") -- COLLOIDALGENIE.scr:37
    ctx:cacheClientFx("SPELL_BLACKSMOKE") -- COLLOIDALGENIE.scr:38
    ctx:cacheSound("sounds\\animsounds\\dragon\\fidget1.wav") -- COLLOIDALGENIE.scr:40
    ctx:cacheSound("sounds\\animsounds\\zombie\\ressurect2.wav") -- COLLOIDALGENIE.scr:41
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:43
end

script.labels["InitColloidalGenie"] = function(ctx)
    -- COLLOIDALGENIE.scr:46
    ctx:self():setModelFilenames("models\\ColloidalWarrior.abc", "skins\\spells\\Shockwave.dtx") -- COLLOIDALGENIE.scr:48
    ctx:self():addEnemy("AIBase") -- COLLOIDALGENIE.scr:52
    ctx:self():addFriend("Player") -- COLLOIDALGENIE.scr:53
    ctx:addTrigger("appear", "AppearWait") -- COLLOIDALGENIE.scr:55
    ctx:onRudeExit("GrantWish", script.labels["GrantWish"]) -- COLLOIDALGENIE.scr:57
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:59
end

script.labels["AppearWait"] = function(ctx)
    -- COLLOIDALGENIE.scr:62
    ctx:state().hAppear = ctx:objectOrNil("sAppearName") -- COLLOIDALGENIE.scr:64
    ctx:state().x, ctx:state().y, ctx:state().z = ctx:object("hAppear"):pos() -- COLLOIDALGENIE.scr:65
    ctx:set("y", "y + 36") -- COLLOIDALGENIE.scr:66
    if ctx:condition("hAppear!=0") then -- COLLOIDALGENIE.scr:68
        ctx:object("hAppear"):doClientFx("SPELL_BLACKSMOKE", "FALSE", "TRUE") -- COLLOIDALGENIE.scr:69
        ctx:wait(0, 2, "Appear") -- COLLOIDALGENIE.scr:70
    end -- COLLOIDALGENIE.scr:71
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:73
end

script.labels["Appear"] = function(ctx)
    -- COLLOIDALGENIE.scr:76
    ctx:object("hAppear"):doClientFx("SPELL_MIST", "FALSE", "TRUE") -- COLLOIDALGENIE.scr:78
    ctx:self():setPos("x", "y", "z") -- COLLOIDALGENIE.scr:80
    ctx:playSound("sounds\\animsounds\\dragon\\fidget1.wav", "DoNothing", 1, 1000, "FALSE", 100) -- COLLOIDALGENIE.scr:82
    ctx:playSound("sounds\\animsounds\\zombie\\ressurect2.wav", "DoNothing", 1, 1000, "FALSE", 100) -- COLLOIDALGENIE.scr:83
    ctx:wait(0, 3, "OfferWish") -- COLLOIDALGENIE.scr:85
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:87
end

script.labels["OfferWish"] = function(ctx)
    -- COLLOIDALGENIE.scr:90
    ctx:removeTrigger("use") -- COLLOIDALGENIE.scr:92
    ctx:doRude(435) -- COLLOIDALGENIE.scr:93
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:95
end

script.labels["GrantWish"] = function(ctx)
    -- COLLOIDALGENIE.scr:98
    ctx:addTrigger("use", "BlockRUDE") -- COLLOIDALGENIE.scr:100
    ctx:onRudeExit("DoNothing", script.labels["DoNothing"]) -- COLLOIDALGENIE.scr:101
    ctx:hasKey(5022, "bHasKey") -- COLLOIDALGENIE.scr:103
    if ctx:condition("bHasKey==TRUE") then -- COLLOIDALGENIE.scr:104
        ctx:giveGold(5000) -- COLLOIDALGENIE.scr:105
    else -- COLLOIDALGENIE.scr:106
        ctx:hasKey(5023, "bHasKey") -- COLLOIDALGENIE.scr:107
        if ctx:condition("bHasKey==TRUE") then -- COLLOIDALGENIE.scr:108
            ctx:giveExp(5000) -- COLLOIDALGENIE.scr:109
        else -- COLLOIDALGENIE.scr:110
            ctx:hasKey(5024, "bHasKey") -- COLLOIDALGENIE.scr:111
            if ctx:condition("bHasKey==TRUE") then -- COLLOIDALGENIE.scr:112
                ctx:randomInt(234, 238, "x") -- COLLOIDALGENIE.scr:113
                ctx:giveItem("x") -- COLLOIDALGENIE.scr:114
            else -- COLLOIDALGENIE.scr:115
                ctx:hasKey(5025, "bHasKey") -- COLLOIDALGENIE.scr:116
                if ctx:condition("bHasKey==TRUE") then -- COLLOIDALGENIE.scr:117
                    ctx:giveAttribute(0, 10, "TRUE", 0) -- COLLOIDALGENIE.scr:118
                end -- COLLOIDALGENIE.scr:119
            end -- COLLOIDALGENIE.scr:120
        end -- COLLOIDALGENIE.scr:121
    end -- COLLOIDALGENIE.scr:122
    ctx:wait(0, 3, "Disappear") -- COLLOIDALGENIE.scr:124
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:126
end

script.labels["Disappear"] = function(ctx)
    -- COLLOIDALGENIE.scr:129
    ctx:object("hAppear"):doClientFx("SPELL_MIST", "FALSE", "TRUE") -- COLLOIDALGENIE.scr:131
    ctx:object("hAppear"):doClientFx("SPELL_BLACKSMOKE", "FALSE", "TRUE") -- COLLOIDALGENIE.scr:132
    ctx:self():remove() -- COLLOIDALGENIE.scr:134
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:136
end

script.labels["BlockRUDE"] = function(ctx)
    -- COLLOIDALGENIE.scr:139
    do return ctx:exit("TRUE") end -- COLLOIDALGENIE.scr:141
end

return script
