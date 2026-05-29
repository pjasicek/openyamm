-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "SCENETEST.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- SceneTest.scr
script.labels["On"] = function(ctx)
    -- SCENETEST.scr:14
    ctx:state().g_hTarget = ctx:objectOrNil("PlayerActor0") -- SCENETEST.scr:18
    ctx:state().g_hCamera = ctx:objectOrNil("SceneCamera0") -- SCENETEST.scr:19
    if ctx:condition("g_hTarget==NULL") then -- SCENETEST.scr:21
        do return ctx:exit("TRUE") end -- SCENETEST.scr:22
    end -- SCENETEST.scr:23
    if ctx:condition("g_hCamera==NULL") then -- SCENETEST.scr:25
        do return ctx:exit("TRUE") end -- SCENETEST.scr:26
    end -- SCENETEST.scr:27
    ctx:trigger("g_hTarget", "ON") -- SCENETEST.scr:29
    ctx:trigger("g_hCamera", "ON") -- SCENETEST.scr:30
    do return ctx:exit("FALSE") end -- SCENETEST.scr:33
end

script.labels["Off"] = function(ctx)
    -- SCENETEST.scr:36
    if ctx:condition("g_hTarget!=NULL") then -- SCENETEST.scr:38
        ctx:trigger("g_hTarget", "OFF") -- SCENETEST.scr:39
    end -- SCENETEST.scr:40
    if ctx:condition("g_hCamera!=NULL") then -- SCENETEST.scr:42
        ctx:trigger("g_hCamera", "OFF") -- SCENETEST.scr:43
    end -- SCENETEST.scr:44
    do return ctx:exit("FALSE") end -- SCENETEST.scr:46
end

script.labels["Main"] = function(ctx)
    -- SCENETEST.scr:49
    -- TraceON
    ctx:addTrigger("ON", "On") -- SCENETEST.scr:54
    ctx:addTrigger("OFF", "Off") -- SCENETEST.scr:55
    do return ctx:exit("") end -- SCENETEST.scr:57
end

return script
