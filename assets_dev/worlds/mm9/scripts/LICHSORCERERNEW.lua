-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "LICHSORCERERNEW.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 1, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 2, path = "CutSceneActor.inc" }

script.labels["Main"] = function(ctx)
    -- LICHSORCERERNEW.scr:12
    ctx:getParam(0, "sDoorName") -- LICHSORCERERNEW.scr:14
    ctx:wait(0, 1, "InitLichSorcererNew") -- LICHSORCERERNEW.scr:16
    do return ctx:exit("TRUE") end -- LICHSORCERERNEW.scr:20
end

script.labels["InitLichSorcererNew"] = function(ctx)
    -- LICHSORCERERNEW.scr:23
    ctx:addTrigger("play", "LookMenacing") -- LICHSORCERERNEW.scr:25
    do return ctx:exit("TRUE") end -- LICHSORCERERNEW.scr:27
end

script.labels["LookMenacing"] = function(ctx)
    -- LICHSORCERERNEW.scr:30
    mm9.gosub(script, ctx, "EffectLoop") -- LICHSORCERERNEW.scr:32
    ctx:state().hDoor = ctx:objectOrNil("sDoorName") -- LICHSORCERERNEW.scr:34
    ctx:self():faceObject(ctx:object("hDoor"), 0, "DoNothing") -- LICHSORCERERNEW.scr:35
    ctx:self():playAnimation("ressurect", "DoNothing") -- LICHSORCERERNEW.scr:37
    ctx:wait(0, 5, "EndScene") -- LICHSORCERERNEW.scr:39
    do return ctx:exit("TRUE") end -- LICHSORCERERNEW.scr:41
end

script.labels["EffectLoop"] = function(ctx)
    -- LICHSORCERERNEW.scr:44
    ctx:self():doClientFx("SPELL_SPIRIT", 0, 1) -- LICHSORCERERNEW.scr:46
    ctx:wait(1, .4, "EffectLoop") -- LICHSORCERERNEW.scr:48
    do return ctx:exit("TRUE") end -- LICHSORCERERNEW.scr:50
end

return script
