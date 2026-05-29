-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "BATTLECAM1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "globals.inc" }

-- BattleCam1.scr
-- 1/5/02
-- timmy
-- does battlefield camera
script.labels["OnPlay"] = function(ctx)
    -- BATTLECAM1.scr:26
    ctx:state().Xpos, ctx:state().Ypos, ctx:state().Zpos = ctx:object("sMarker"):pos() -- BATTLECAM1.scr:29-30
    ctx:self():moveToPos("xpos", "Ypos", "Zpos", "nSpeed", "OnArrive") -- BATTLECAM1.scr:31
    do return ctx:exit("") end -- BATTLECAM1.scr:32
end

script.labels["OnArrive"] = function(ctx)
    -- BATTLECAM1.scr:35
    ctx:object("sven"):trigger("Done") -- BATTLECAM1.scr:38-39
    do return ctx:exit("") end -- BATTLECAM1.scr:40
end

script.labels["Main"] = function(ctx)
    -- BATTLECAM1.scr:42
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("Play", "OnPlay") -- BATTLECAM1.scr:47
    ctx:getParam(0, "sMarker") -- BATTLECAM1.scr:48
    ctx:getParam(1, "nSpeed") -- BATTLECAM1.scr:49
    do return ctx:exit("") end -- BATTLECAM1.scr:50
end

return script
