-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BC_TREASURECHEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }

-- BC_TreasureChest.scr
-- by SJR
-- Purpose:
script.labels["Main"] = function(ctx)
    -- BC_TREASURECHEST.scr:15
    ctx:getParam(0, "CHEST_TRAP") -- BC_TREASURECHEST.scr:17
    ctx:addTrigger("open", "PlayOpenAnim") -- BC_TREASURECHEST.scr:19
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- BC_TREASURECHEST.scr:21
    do return ctx:exit("TRUE") end -- BC_TREASURECHEST.scr:23
end

script.labels["CacheFiles"] = function(ctx)
    -- BC_TREASURECHEST.scr:26
    if ctx:condition("CHEST_TRAP==TRUE") then -- BC_TREASURECHEST.scr:28
        ctx:cacheClientFx("SPELL_COLUMNOFFIRE") -- BC_TREASURECHEST.scr:29
        ctx:cacheSound("sounds\\door\\doorlatch01.wav") -- BC_TREASURECHEST.scr:30
    end -- BC_TREASURECHEST.scr:31
    do return ctx:exit("TRUE") end -- BC_TREASURECHEST.scr:33
end

script.labels["PlayOpenAnim"] = function(ctx)
    -- BC_TREASURECHEST.scr:36
    if ctx:condition("CHEST_TRAP==TRUE") then -- BC_TREASURECHEST.scr:38
        ctx:getParam(0, "hOpener") -- BC_TREASURECHEST.scr:39
        ctx:self():playAnimation("open", "SpringTrap") -- BC_TREASURECHEST.scr:40
    else -- BC_TREASURECHEST.scr:41
        ctx:self():playAnimation("open", "HoldOpenAnim") -- BC_TREASURECHEST.scr:42
    end -- BC_TREASURECHEST.scr:43
    do return ctx:exit("TRUE") end -- BC_TREASURECHEST.scr:45
end

script.labels["HoldOpenAnim"] = function(ctx)
    -- BC_TREASURECHEST.scr:48
    ctx:wait(0, 2, "PlayCloseAnim") -- BC_TREASURECHEST.scr:50
    do return ctx:exit("TRUE") end -- BC_TREASURECHEST.scr:52
end

script.labels["PlayCloseAnim"] = function(ctx)
    -- BC_TREASURECHEST.scr:55
    ctx:self():playAnimation("Close", "DoNothing") -- BC_TREASURECHEST.scr:57
    do return ctx:exit("TRUE") end -- BC_TREASURECHEST.scr:59
end

script.labels["SpringTrap"] = function(ctx)
    -- BC_TREASURECHEST.scr:62
    ctx:object("hOpener"):doClientFx("SPELL_COLUMNOFFIRE", "FALSE", "TRUE") -- BC_TREASURECHEST.scr:64
    ctx:playSound("sounds\\door\\doorlatch01.wav", "DoNothing", 1, 1000, "FALSE", 100) -- BC_TREASURECHEST.scr:66
    ctx:wait(1, 1, "KillTheGuy") -- BC_TREASURECHEST.scr:68
    mm9.gosub(script, ctx, "HoldOpenAnim") -- BC_TREASURECHEST.scr:70
    do return ctx:exit("TRUE") end -- BC_TREASURECHEST.scr:72
end

script.labels["KillTheGuy"] = function(ctx)
    -- BC_TREASURECHEST.scr:75
    ctx:trigger("hOpener", "destroy") -- BC_TREASURECHEST.scr:77
    ctx:wait(2, 2, "RemoveTheGuy") -- BC_TREASURECHEST.scr:79
    do return ctx:exit("TRUE") end -- BC_TREASURECHEST.scr:81
end

script.labels["RemoveTheGuy"] = function(ctx)
    -- BC_TREASURECHEST.scr:84
    if ctx:condition("hOpener!=0") then -- BC_TREASURECHEST.scr:86
        ctx:object("hOpener"):remove() -- BC_TREASURECHEST.scr:87
    end -- BC_TREASURECHEST.scr:88
    do return ctx:exit("TRUE") end -- BC_TREASURECHEST.scr:90
end

return script
