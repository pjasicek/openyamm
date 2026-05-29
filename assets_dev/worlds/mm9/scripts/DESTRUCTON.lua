-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DESTRUCTON.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- DestructOn.scr
-- By Timmy
-- set destructable brushes to On
-- 1/2/02
script.labels["DestroyMe"] = function(ctx)
    -- DESTRUCTON.scr:16
    ctx:trigger("g_hmyobject", "destroy") -- DESTRUCTON.scr:20
    do return ctx:exit("") end -- DESTRUCTON.scr:21
end

script.labels["OnDamageOn"] = function(ctx)
    -- DESTRUCTON.scr:25
    ctx:self():setNumberProperty("CanDamage", "TRUE") -- DESTRUCTON.scr:28
    do return ctx:exit("") end -- DESTRUCTON.scr:30
end

script.labels["Main"] = function(ctx)
    -- DESTRUCTON.scr:33
    -- TraceOn ;delete me!!
    ctx:addTrigger("DamageOn", "OnDamageOn") -- DESTRUCTON.scr:37
    ctx:onEvent("OnDamage", "DestroyMe") -- DESTRUCTON.scr:38
    do return ctx:exit("") end -- DESTRUCTON.scr:39
end

return script
