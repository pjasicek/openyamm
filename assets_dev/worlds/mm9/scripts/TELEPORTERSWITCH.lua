-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TELEPORTERSWITCH.scr"
script.includes = {}
script.labels = {}


-- TeleporterSwitch.scr
-- by SJR
-- 01-01-02
-- Purpose:function as a destination switcher.
-- ScriptParams:
-- p0 = name teleporter to switch
-- p1 = name of destination
script.labels["Main"] = function(ctx)
    -- TELEPORTERSWITCH.scr:23
    ctx:getParam(0, "TELEPORTER_NAME") -- TELEPORTERSWITCH.scr:25
    ctx:getParam(1, "DESTINATION_NAME") -- TELEPORTERSWITCH.scr:26
    ctx:getParam(2, "EFFECTS_NAME") -- TELEPORTERSWITCH.scr:27
    ctx:setConsoleStrVar("TELEPORTER_DESTINATION", "\"\"") -- TELEPORTERSWITCH.scr:29
    ctx:addTrigger("use", "SetDestination") -- TELEPORTERSWITCH.scr:31
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- TELEPORTERSWITCH.scr:33
    do return ctx:exit(1) end -- TELEPORTERSWITCH.scr:35
end

script.labels["CacheFiles"] = function(ctx)
    -- TELEPORTERSWITCH.scr:38
    ctx:cacheSound("sounds\\magic\\wizardeyeloop.wav") -- TELEPORTERSWITCH.scr:40
    ctx:cacheClientFx("SPELL_SPELLREAVER") -- TELEPORTERSWITCH.scr:42
    do return ctx:exit(1) end -- TELEPORTERSWITCH.scr:44
end

script.labels["SetDestination"] = function(ctx)
    -- TELEPORTERSWITCH.scr:47
    ctx:setConsoleStrVar("TELEPORTER_DESTINATION", "DESTINATION_NAME") -- TELEPORTERSWITCH.scr:49
    if ctx:condition("hTeleporter==0") then -- TELEPORTERSWITCH.scr:51
        ctx:state().hTeleporter = ctx:objectOrNil("TELEPORTER_NAME") -- TELEPORTERSWITCH.scr:52
    end -- TELEPORTERSWITCH.scr:53
    if ctx:condition("hEffects==0") then -- TELEPORTERSWITCH.scr:54
        ctx:state().hEffects = ctx:objectOrNil("EFFECTS_NAME") -- TELEPORTERSWITCH.scr:55
    end -- TELEPORTERSWITCH.scr:56
    if ctx:condition("hTeleporter!=0") then -- TELEPORTERSWITCH.scr:58
        ctx:trigger("hTeleporter", "on") -- TELEPORTERSWITCH.scr:59
        ctx:trigger("hTeleporter", "update") -- TELEPORTERSWITCH.scr:60
    end -- TELEPORTERSWITCH.scr:61
    if ctx:condition("hEffects!=0") then -- TELEPORTERSWITCH.scr:63
        ctx:playSound("sounds\\magic\\wizardeyeloop.wav") -- TELEPORTERSWITCH.scr:64
        ctx:object("hTeleporter"):doClientFx("SPELL_SPELLREAVER", 0, 1) -- TELEPORTERSWITCH.scr:65
        mm9.gosub(script, ctx, "TurnEffectsOn") -- TELEPORTERSWITCH.scr:66
        ctx:wait(0, "EFFECTS_WAIT_TIME", "TurnEffectsOff") -- TELEPORTERSWITCH.scr:67
    end -- TELEPORTERSWITCH.scr:68
    do return ctx:exit(1) end -- TELEPORTERSWITCH.scr:70
end

script.labels["TurnEffectsOn"] = function(ctx)
    -- TELEPORTERSWITCH.scr:73
    ctx:removeTrigger("use") -- TELEPORTERSWITCH.scr:75
    ctx:trigger("hEffects", "on") -- TELEPORTERSWITCH.scr:76
    do return ctx:exit(1) end -- TELEPORTERSWITCH.scr:78
end

script.labels["TurnEffectsOff"] = function(ctx)
    -- TELEPORTERSWITCH.scr:81
    ctx:trigger("hEffects", "off") -- TELEPORTERSWITCH.scr:83
    ctx:addTrigger("use", "SetDestination") -- TELEPORTERSWITCH.scr:84
    do return ctx:exit(1) end -- TELEPORTERSWITCH.scr:86
end

return script
