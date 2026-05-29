-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "TM_FALLINGTORCH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "Globals.inc" }

-- TM_FallingTorch.scr
-- kd
-- 10-30-01
-- Makes the torch fall to the ground.
-- Nothing slick or fancy
script.labels["StopHere"] = function(ctx)
    -- TM_FALLINGTORCH.scr:22
    do return ctx:exit("TRUE") end -- TM_FALLINGTORCH.scr:24
end

script.labels["MoveToMarker"] = function(ctx)
    -- TM_FALLINGTORCH.scr:26
    ctx:object("TorchHolder0"):trigger("Destroy") -- TM_FALLINGTORCH.scr:28-29
    ctx:trigger("hFire", "Fall") -- TM_FALLINGTORCH.scr:30
    ctx:self():rotate(0, 0, 1, -90, 90, "DoNothing") -- TM_FALLINGTORCH.scr:31
    ctx:self():moveToPos("nVarX", "nVarY", "nVarZ", 180, "StopHere") -- TM_FALLINGTORCH.scr:32
    do return ctx:exit("") end -- TM_FALLINGTORCH.scr:33
end

script.labels["Main2"] = function(ctx)
    -- TM_FALLINGTORCH.scr:35
    ctx:state().hFire = ctx:objectOrNil("FallingTorchFire0") -- TM_FALLINGTORCH.scr:37
    ctx:state().nVarX, ctx:state().nVarY, ctx:state().nVarZ = ctx:object("FallingTorchMarker0"):pos() -- TM_FALLINGTORCH.scr:38-39
    ctx:onEvent("OnDamage", "MoveToMarker") -- TM_FALLINGTORCH.scr:40
    do return ctx:exit("TRUE") end -- TM_FALLINGTORCH.scr:41
end

script.labels["Main"] = function(ctx)
    -- TM_FALLINGTORCH.scr:43
    ctx:addTrigger("Hit", "MoveToMarker") -- TM_FALLINGTORCH.scr:45
    ctx:wait(0, .1, "main2") -- TM_FALLINGTORCH.scr:46
    do return ctx:exit("TRUE") end -- TM_FALLINGTORCH.scr:47
end

return script
