-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "RT_COUNTERBALANCE.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 11, path = "Globals.inc" }
script.includes[#script.includes + 1] = { line = 12, path = "Flags.inc" }

-- RT_CounterBalance.scr
-- Karl Drown 11-13-01
-- Super simple "Move My World Object" script.
script.labels["StopHere"] = function(ctx)
    -- RT_COUNTERBALANCE.scr:23
    ctx:playSound("Sounds\\Door\\doorslammetal01.wav", "DoNothing", "hDummy", 400, "FALSE", 100) -- RT_COUNTERBALANCE.scr:25
    ctx:state().hCrypt = nil -- RT_COUNTERBALANCE.scr:26
    ctx:object("DB_Crypt0"):trigger("Destroy") -- RT_COUNTERBALANCE.scr:27-28
    do return ctx:exit("TRUE") end -- RT_COUNTERBALANCE.scr:29
end

script.labels["MoveToMarker"] = function(ctx)
    -- RT_COUNTERBALANCE.scr:31
    ctx:self():setFlag("FLAG_GOTHRUWORLD", true) -- RT_COUNTERBALANCE.scr:34
    -- playsound Sounds\Events\boulderroll.wav DoNothing hDummy 1000 TRUE 100
    ctx:state().nVarX, ctx:state().nVarY, ctx:state().nVarZ = ctx:object("CryptMarker0"):pos() -- RT_COUNTERBALANCE.scr:36-37
    ctx:self():moveToPos("nVarX", "nVarY", "nVarZ", 300, "StopHere") -- RT_COUNTERBALANCE.scr:38
    do return ctx:exit("") end -- RT_COUNTERBALANCE.scr:39
end

script.labels["Main"] = function(ctx)
    -- RT_COUNTERBALANCE.scr:41
    ctx:addTrigger("Fall", "MoveToMarker") -- RT_COUNTERBALANCE.scr:43
    ctx:onEvent("OnDamage", "MoveToMarker") -- RT_COUNTERBALANCE.scr:44
    do return ctx:exit("") end -- RT_COUNTERBALANCE.scr:45
end

return script
