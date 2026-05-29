-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ILSFIREBOOK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 6, path = "BaseGlobals.inc" }

-- ILSfirebook.scr
-- timmy (+ SJR 01-10-02)
-- fires a shooter at player
script.labels["Main"] = function(ctx)
    -- ILSFIREBOOK.scr:17
    ctx:getParam(0, "sShooterName") -- ILSFIREBOOK.scr:19
    ctx:addTrigger("use", "CastSpell") -- ILSFIREBOOK.scr:21
    ctx:onEvent("OnCacheFiles", "CacheFiles") -- ILSFIREBOOK.scr:23
    do return ctx:exit("TRUE") end -- ILSFIREBOOK.scr:27
end

script.labels["CacheFiles"] = function(ctx)
    -- ILSFIREBOOK.scr:30
    ctx:cacheClientFx("SPELL_SPARKLIES") -- ILSFIREBOOK.scr:32
    do return ctx:exit("TRUE") end -- ILSFIREBOOK.scr:34
end

script.labels["CastSpell"] = function(ctx)
    -- ILSFIREBOOK.scr:37
    if ctx:condition("hShooter==0") then -- ILSFIREBOOK.scr:39
        ctx:state().hShooter = ctx:objectOrNil("sShooterName") -- ILSFIREBOOK.scr:40
    end -- ILSFIREBOOK.scr:41
    if ctx:condition("bOpen==FALSE") then -- ILSFIREBOOK.scr:43
        ctx:state().bOpen = true -- ILSFIREBOOK.scr:44
        ctx:self():playAnimation("OpenBook", "TriggerShooter") -- ILSFIREBOOK.scr:45
    else -- ILSFIREBOOK.scr:46
        mm9.gosub(script, ctx, "TriggerShooter") -- ILSFIREBOOK.scr:47
    end -- ILSFIREBOOK.scr:48
    do return ctx:exit("TRUE") end -- ILSFIREBOOK.scr:50
end

script.labels["TriggerShooter"] = function(ctx)
    -- ILSFIREBOOK.scr:53
    ctx:self():doClientFx("SPELL_SPARKLIES", "FALSE", "TRUE") -- ILSFIREBOOK.scr:55
    if ctx:condition("hShooter!=0") then -- ILSFIREBOOK.scr:57
        ctx:trigger("hShooter", "shoot") -- ILSFIREBOOK.scr:58
    end -- ILSFIREBOOK.scr:59
    do return ctx:exit("TRUE") end -- ILSFIREBOOK.scr:61
end

return script
