-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EBORACONCUBINE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "baseMelee.inc" }

-- EboraConcubine.scr
-- By L. Dean Gibson II
-- Ebora's Concubine's script in the bathhouse
-- SJR
script.labels["OnLaunchDone"] = function(ctx)
    -- EBORACONCUBINE.scr:13
    mm9.gosub(script, ctx, "SetupTarget") -- EBORACONCUBINE.scr:15
    mm9.gosub(script, ctx, "AggressiveStart") -- EBORACONCUBINE.scr:16
    do return ctx:exit("TRUE") end -- EBORACONCUBINE.scr:18
end

script.labels["OnFoundPlayer"] = function(ctx)
    -- EBORACONCUBINE.scr:22
    ctx:onEvent("OnFoundPlayer", "DoNothing") -- EBORACONCUBINE.scr:24
    ctx:getParam(0, "g_hTarget") -- EBORACONCUBINE.scr:26
    ctx:self():playAnimation("launch", "OnLaunchDone") -- EBORACONCUBINE.scr:28
    do return ctx:exit("TRUE") end -- EBORACONCUBINE.scr:30
end

script.labels["OnDeath"] = function(ctx)
    -- EBORACONCUBINE.scr:33
    -- message to ebora of our death
    ctx:object("Ebora"):trigger("DeadConcubine") -- EBORACONCUBINE.scr:36-37
    mm9.gosub(script, ctx, "OnDeath") -- EBORACONCUBINE.scr:39
    do return ctx:exit("TRUE") end -- EBORACONCUBINE.scr:41
end

script.labels["InitEboraConcubine"] = function(ctx)
    -- EBORACONCUBINE.scr:44
    ctx:randomInt(0, 3, "g_nTemp") -- EBORACONCUBINE.scr:46
    if ctx:condition("g_nTemp==0") then -- EBORACONCUBINE.scr:48
        ctx:self():setModelFilenames("models\\ebora.abc", "skins\\Siren1.dtx") -- EBORACONCUBINE.scr:49
    else -- EBORACONCUBINE.scr:50
        if ctx:condition("g_nTemp==1") then -- EBORACONCUBINE.scr:51
            ctx:self():setModelFilenames("models\\ebora.abc", "skins\\Siren2.dtx") -- EBORACONCUBINE.scr:52
        else -- EBORACONCUBINE.scr:53
            if ctx:condition("g_nTemp==2") then -- EBORACONCUBINE.scr:54
                ctx:self():setModelFilenames("models\\ebora.abc", "skins\\Siren3.dtx") -- EBORACONCUBINE.scr:55
            else -- EBORACONCUBINE.scr:56
                if ctx:condition("g_nTemp==3") then -- EBORACONCUBINE.scr:57
                    ctx:self():setModelFilenames("models\\ebora.abc", "skins\\Siren4.dtx") -- EBORACONCUBINE.scr:58
                end -- EBORACONCUBINE.scr:59
            end -- EBORACONCUBINE.scr:60
        end -- EBORACONCUBINE.scr:61
    end -- EBORACONCUBINE.scr:62
    mm9.gosub(script, ctx, "BaseInit") -- EBORACONCUBINE.scr:64
    ctx:onEvent("OnDeath", "OnDeath") -- EBORACONCUBINE.scr:66
    ctx:onEvent("OnFoundPlayer", "OnFoundPlayer") -- EBORACONCUBINE.scr:67
    ctx:self():setIdle() -- EBORACONCUBINE.scr:69
    do return ctx:exit("TRUE") end -- EBORACONCUBINE.scr:71
end

script.labels["Main"] = function(ctx)
    -- EBORACONCUBINE.scr:74
    ctx:onEvent("OnPostStartWorld", "InitEboraConcubine") -- EBORACONCUBINE.scr:76
    do return ctx:exit("TRUE") end -- EBORACONCUBINE.scr:78
end

return script
