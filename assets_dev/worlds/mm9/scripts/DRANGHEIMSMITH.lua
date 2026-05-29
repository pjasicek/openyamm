-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRANGHEIMSMITH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }

-- DrangheimPrisoner.scr
-- SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- DRANGHEIMSMITH.scr:29
    ctx:getParam(0, "bBearer") -- DRANGHEIMSMITH.scr:31
    if ctx:condition("bBearer==0") then -- DRANGHEIMSMITH.scr:33
        ctx:state().hRack = ctx:self() -- DRANGHEIMSMITH.scr:34
        ctx:object("hRack"):remove() -- DRANGHEIMSMITH.scr:35
        do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:36
    end -- DRANGHEIMSMITH.scr:37
    ctx:onEvent("OnPostStartWorld", "InitDrangheimSmith") -- DRANGHEIMSMITH.scr:39
    ctx:onEvent("OnPostMiniSaveLoad", "InitDrangheimSmith") -- DRANGHEIMSMITH.scr:40
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- DRANGHEIMSMITH.scr:41
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:43
end

script.labels["CacheFiles"] = function(ctx)
    -- DRANGHEIMSMITH.scr:46
    ctx:cacheSound("sounds\\events\\metalmetal01.wav\"") -- DRANGHEIMSMITH.scr:48
    ctx:cacheSound("sounds\\events\\metalmetal02.wav\"") -- DRANGHEIMSMITH.scr:49
    ctx:cacheSound("sounds\\events\\metalmetal03.wav\"") -- DRANGHEIMSMITH.scr:50
    ctx:cacheSound("sounds\\events\\metalmetal04.wav\"") -- DRANGHEIMSMITH.scr:51
    ctx:cacheSound("sounds\\events\\metalmetal05.wav\"") -- DRANGHEIMSMITH.scr:52
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:54
end

script.labels["InitDrangheimSmith"] = function(ctx)
    -- DRANGHEIMSMITH.scr:57
    ctx:state().hAnvil = ctx:objectOrNil("sAnvilName") -- DRANGHEIMSMITH.scr:59
    ctx:state().hRack = ctx:objectOrNil("sRackName") -- DRANGHEIMSMITH.scr:60
    ctx:state().hSteam = ctx:objectOrNil("sSteamName") -- DRANGHEIMSMITH.scr:61
    ctx:state().hFire = ctx:objectOrNil("sFireName") -- DRANGHEIMSMITH.scr:62
    ctx:onEvent("OnDeath", "DetachItem") -- DRANGHEIMSMITH.scr:64
    ctx:addTrigger("off", "TurnOff") -- DRANGHEIMSMITH.scr:66
    ctx:addTrigger("on", "OnReturnedWeapon") -- DRANGHEIMSMITH.scr:67
    mm9.gosub(script, ctx, "InitStrings") -- DRANGHEIMSMITH.scr:69
    mm9.gosub(script, ctx, "OnReturnedWeapon") -- DRANGHEIMSMITH.scr:70
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:72
end

script.labels["AnvilLoop"] = function(ctx)
    -- DRANGHEIMSMITH.scr:75
    if ctx:condition("bQuit==TRUE") then -- DRANGHEIMSMITH.scr:77
        ctx:state().bQuit = false -- DRANGHEIMSMITH.scr:78
        do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:79
    else -- DRANGHEIMSMITH.scr:80
        if ctx:condition("nCounter==0") then -- DRANGHEIMSMITH.scr:82
            ctx:state().nCounter = 10 -- DRANGHEIMSMITH.scr:83
            mm9.gosub(script, ctx, "CoolWeapon") -- DRANGHEIMSMITH.scr:84
            do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:85
        end -- DRANGHEIMSMITH.scr:86
    end -- DRANGHEIMSMITH.scr:87
    ctx:self():faceObject(ctx:object("hAnvil"), 180, "DoNothing") -- DRANGHEIMSMITH.scr:89
    mm9.gosub(script, ctx, "PlayRandom") -- DRANGHEIMSMITH.scr:90
    ctx:set("nCounter", "nCounter - bBearer") -- DRANGHEIMSMITH.scr:91
    ctx:wait(0, 3, "AnvilLoop") -- DRANGHEIMSMITH.scr:92
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:94
end

script.labels["CoolWeapon"] = function(ctx)
    -- DRANGHEIMSMITH.scr:97
    mm9.gosub(script, ctx, "AttachSword") -- DRANGHEIMSMITH.scr:99
    ctx:self():walkTo(ctx:object("hSteam"), 40, "OnCooledWeapon") -- DRANGHEIMSMITH.scr:101
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:103
end

script.labels["OnCooledWeapon"] = function(ctx)
    -- DRANGHEIMSMITH.scr:106
    ctx:self():stop() -- DRANGHEIMSMITH.scr:108
    ctx:self():faceObject(ctx:object("hSteam"), 180, "DoNothing") -- DRANGHEIMSMITH.scr:109
    ctx:trigger("hSteam", "on") -- DRANGHEIMSMITH.scr:110
    ctx:wait(0, 5, "ReturnWeapon") -- DRANGHEIMSMITH.scr:111
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:113
end

script.labels["ReturnWeapon"] = function(ctx)
    -- DRANGHEIMSMITH.scr:116
    ctx:self():stop() -- DRANGHEIMSMITH.scr:118
    ctx:trigger("hSteam", "off") -- DRANGHEIMSMITH.scr:119
    ctx:self():walkTo(ctx:object("hRack"), 5, "OnReturnedWeapon") -- DRANGHEIMSMITH.scr:120
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:122
end

script.labels["OnReturnedWeapon"] = function(ctx)
    -- DRANGHEIMSMITH.scr:125
    ctx:self():stop() -- DRANGHEIMSMITH.scr:127
    mm9.gosub(script, ctx, "AttachHammer") -- DRANGHEIMSMITH.scr:128
    ctx:self():walkTo(ctx:object("hAnvil"), 10, "StartOver") -- DRANGHEIMSMITH.scr:130
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:132
end

script.labels["StartOver"] = function(ctx)
    -- DRANGHEIMSMITH.scr:135
    ctx:self():stop() -- DRANGHEIMSMITH.scr:137
    ctx:wait(0, 5, "AnvilLoop") -- DRANGHEIMSMITH.scr:138
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:140
end

script.labels["PlayRandom"] = function(ctx)
    -- DRANGHEIMSMITH.scr:143
    ctx:self():playAnimation("HAttack1", "PlayRandomSound") -- DRANGHEIMSMITH.scr:145
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:147
end

script.labels["PlayRandomSound"] = function(ctx)
    -- DRANGHEIMSMITH.scr:150
    ctx:randomInt(0, 4, "nTemp") -- DRANGHEIMSMITH.scr:152
    ctx:arrayGet("spSounds", "nTemp", "sSound") -- DRANGHEIMSMITH.scr:153
    ctx:playSound("sSound", "DoNothing", 1, 500, 0, 100) -- DRANGHEIMSMITH.scr:154
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:156
end

script.labels["InitStrings"] = function(ctx)
    -- DRANGHEIMSMITH.scr:159
    ctx:arrayPut("spSounds", 0, "sounds\\events\\metalmetal01.wav") -- DRANGHEIMSMITH.scr:161
    ctx:arrayPut("spSounds", 1, "sounds\\events\\metalmetal02.wav") -- DRANGHEIMSMITH.scr:162
    ctx:arrayPut("spSounds", 2, "sounds\\events\\metalmetal03.wav") -- DRANGHEIMSMITH.scr:163
    ctx:arrayPut("spSounds", 3, "sounds\\events\\metalmetal04.wav") -- DRANGHEIMSMITH.scr:164
    ctx:arrayPut("spSounds", 4, "sounds\\events\\metalmetal05.wav") -- DRANGHEIMSMITH.scr:165
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:167
end

script.labels["TurnOff"] = function(ctx)
    -- DRANGHEIMSMITH.scr:170
    ctx:self():stop() -- DRANGHEIMSMITH.scr:172
    ctx:state().bQuit = true -- DRANGHEIMSMITH.scr:173
    -- GetObjectHandle MarkerWait, hDummy
    -- RunTo hDummy, 10, StopMoving
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:177
end

script.labels["AttachHammer"] = function(ctx)
    -- DRANGHEIMSMITH.scr:180
    mm9.gosub(script, ctx, "DetachItem") -- DRANGHEIMSMITH.scr:182
    ctx:self():attachProp("hammer.abc", "hammer.dtx", "rhand1", ctx:object("hWeapon")) -- DRANGHEIMSMITH.scr:184
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:186
end

script.labels["AttachSword"] = function(ctx)
    -- DRANGHEIMSMITH.scr:189
    mm9.gosub(script, ctx, "DetachItem") -- DRANGHEIMSMITH.scr:191
    ctx:self():attachProp("kirasword.abc", "kirasword.dtx", "rhand1", ctx:object("hWeapon")) -- DRANGHEIMSMITH.scr:193
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:195
end

script.labels["DetachItem"] = function(ctx)
    -- DRANGHEIMSMITH.scr:198
    if ctx:condition("hWeapon!=0") then -- DRANGHEIMSMITH.scr:200
        ctx:self():detachProp(ctx:object("hWeapon"), "FALSE") -- DRANGHEIMSMITH.scr:201
        ctx:object("hWeapon"):remove() -- DRANGHEIMSMITH.scr:202
        ctx:state().hWeapon = nil -- DRANGHEIMSMITH.scr:203
    end -- DRANGHEIMSMITH.scr:204
    do return ctx:exit("TRUE") end -- DRANGHEIMSMITH.scr:206
end

return script
