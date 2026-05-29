-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "WIZARDEFFECT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "flags.inc" }

-- WizardEffect.scr
-- by SJR
-- 01-01-02
-- Purpose:
script.labels["Main"] = function(ctx)
    -- WIZARDEFFECT.scr:21
    ctx:getParam(0, "sLocationName") -- WIZARDEFFECT.scr:23
    mm9.gosub(script, ctx, "InitWizardEffect") -- WIZARDEFFECT.scr:25
    do return ctx:exit("TRUE") end -- WIZARDEFFECT.scr:27
end

script.labels["InitWizardEffect"] = function(ctx)
    -- WIZARDEFFECT.scr:30
    ctx:self():setFlag("FLAG_VISIBLE", true) -- WIZARDEFFECT.scr:33
    ctx:addTrigger("play", "PlayConjureEffect") -- WIZARDEFFECT.scr:35
    ctx:addTrigger("shoot", "PlayShootEffect") -- WIZARDEFFECT.scr:36
    do return ctx:exit("TRUE") end -- WIZARDEFFECT.scr:38
end

script.labels["PlayConjureEffect"] = function(ctx)
    -- WIZARDEFFECT.scr:41
    ctx:getParam(0, "hCaster") -- WIZARDEFFECT.scr:43
    ctx:object("hCaster"):doClientFx("SPELL_SPARKLIES", "FALSE", "TRUE") -- WIZARDEFFECT.scr:45
    ctx:self():doClientFx("SPELL_GREENDOTS", "FALSE", "TRUE") -- WIZARDEFFECT.scr:46
    ctx:state().hLocation = ctx:objectOrNil("sLocationName") -- WIZARDEFFECT.scr:48
    ctx:self():faceObject(ctx:object("hLocation")) -- WIZARDEFFECT.scr:49
    do return ctx:exit("TRUE") end -- WIZARDEFFECT.scr:51
end

script.labels["PlayShootEffect"] = function(ctx)
    -- WIZARDEFFECT.scr:54
    ctx:object("hLocation"):doClientFx("SPELL_BUGS", "FALSE", "TRUE") -- WIZARDEFFECT.scr:56
    do return ctx:exit("FALSE") end -- WIZARDEFFECT.scr:58
end

return script
