-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "EBORACAM1.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "BaseGlobals.inc" }

-- EboraCam1.scr
-- By L. Dean Gibson II
-- Ebora's Camera script in the bathhouse...
-- SJR
script.labels["CameraOn"] = function(ctx)
    -- EBORACAM1.scr:15
    ctx:state().hEbora = ctx:objectOrNil("Ebora") -- EBORACAM1.scr:17
    ctx:self():faceObject(ctx:object("hEbora"), 0, "DoNothing") -- EBORACAM1.scr:18
    do return ctx:exit("FALSE") end -- EBORACAM1.scr:20
end

script.labels["Main"] = function(ctx)
    -- EBORACAM1.scr:23
    ctx:addTrigger("on", "CameraOn") -- EBORACAM1.scr:25
    do return ctx:exit("TRUE") end -- EBORACAM1.scr:27
end

return script
