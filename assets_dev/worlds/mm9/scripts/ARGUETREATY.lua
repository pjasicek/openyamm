-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ARGUETREATY.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- arguetreaty.scr
-- 1/5/02
-- timmy
-- does battlefield camera
script.labels["OnPlay"] = function(ctx)
    -- ARGUETREATY.scr:27
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("sMarker"):pos() -- ARGUETREATY.scr:32-33
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", "nSpeed", "DoNothing") -- ARGUETREATY.scr:34
    do return ctx:exit("") end -- ARGUETREATY.scr:35
end

script.labels["Init"] = function(ctx)
    -- ARGUETREATY.scr:38
    ctx:self():loopAnimation("Down", 0, "DoNothing") -- ARGUETREATY.scr:40
    do return ctx:exit("") end -- ARGUETREATY.scr:41
end

script.labels["Main"] = function(ctx)
    -- ARGUETREATY.scr:43
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- ARGUETREATY.scr:48
    ctx:getParam(0, "sMarker") -- ARGUETREATY.scr:49
    ctx:onEvent("OnPostStartWorld", "Init") -- ARGUETREATY.scr:50
    ctx:onEvent("OnPostMiniSaveLoad", "Init") -- ARGUETREATY.scr:51
    ctx:onEvent("OnPostSaveLoad", "Init") -- ARGUETREATY.scr:52
    ctx:wait(1, .1, "Init") -- ARGUETREATY.scr:53
    do return ctx:exit("") end -- ARGUETREATY.scr:54
end

return script
