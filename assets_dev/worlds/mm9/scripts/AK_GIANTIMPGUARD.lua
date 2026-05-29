-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "AK_GIANTIMPGUARD.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "baseMelee.inc" }
script.includes[#script.includes + 1] = { line = 7, path = "flags.inc" }

-- AK_GiantImp.scr
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- AK_GIANTIMPGUARD.scr:10
    ctx:self():addFriend("Player") -- AK_GIANTIMPGUARD.scr:12
    ctx:self():addEnemy("Imp") -- AK_GIANTIMPGUARD.scr:13
    ctx:self():setStat("gravity", "FALSE") -- AK_GIANTIMPGUARD.scr:17
    ctx:self():setFlag("FLAG_SOLID", false) -- AK_GIANTIMPGUARD.scr:18
    ctx:self():setFlag("FLAG_VISIBLE", false) -- AK_GIANTIMPGUARD.scr:19
    ctx:addTrigger("appear", "Appear") -- AK_GIANTIMPGUARD.scr:21
    do return ctx:exit("TRUE") end -- AK_GIANTIMPGUARD.scr:23
end

script.labels["Appear"] = function(ctx)
    -- AK_GIANTIMPGUARD.scr:26
    -- appear, run to impy, fight, and die
    ctx:getParam(0, "g_hTarget") -- AK_GIANTIMPGUARD.scr:29
    ctx:self():setFlag("FLAG_SOLID", true) -- AK_GIANTIMPGUARD.scr:31
    ctx:self():setFlag("FLAG_VISIBLE", true) -- AK_GIANTIMPGUARD.scr:32
    ctx:self():setStat("gravity", "TRUE") -- AK_GIANTIMPGUARD.scr:33
    mm9.gosub(script, ctx, "BaseInit") -- AK_GIANTIMPGUARD.scr:35
    ctx:state().g_hTarget = ctx:objectOrNil("GiantImp") -- AK_GIANTIMPGUARD.scr:36
    mm9.gosub(script, ctx, "SetupTarget") -- AK_GIANTIMPGUARD.scr:37
    mm9.gosub(script, ctx, "AggressiveStart") -- AK_GIANTIMPGUARD.scr:38
    ctx:onEvent("OnDamage", "OnDamage") -- AK_GIANTIMPGUARD.scr:39
    do return ctx:exit("TRUE") end -- AK_GIANTIMPGUARD.scr:41
end

script.labels["OnDamage"] = function(ctx)
    -- AK_GIANTIMPGUARD.scr:44
    -- die as soon as impy hits us
    ctx:self():die() -- AK_GIANTIMPGUARD.scr:47
    do return ctx:exit("TRUE") end -- AK_GIANTIMPGUARD.scr:49
end

return script
