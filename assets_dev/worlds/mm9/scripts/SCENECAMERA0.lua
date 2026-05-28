-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SCENECAMERA0.scr"
script.includes = {}
script.labels = {}


-- SceneCamera0.scr
script.labels["On"] = function(ctx)
    -- SCENECAMERA0.scr:5
    ctx:command("getobjecthandle", "PlayerActor0, g_hObject") -- SCENECAMERA0.scr:6
    ctx:command("target", "g_hObject") -- SCENECAMERA0.scr:7
    do return ctx:exit(0) end -- SCENECAMERA0.scr:8
end

script.labels["Main"] = function(ctx)
    -- SCENECAMERA0.scr:10
    ctx:addTrigger("ON", "On") -- SCENECAMERA0.scr:12
    do return ctx:exit("") end -- SCENECAMERA0.scr:13
end

return script
