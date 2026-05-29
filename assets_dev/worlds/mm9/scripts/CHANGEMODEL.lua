-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "CHANGEMODEL.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }
script.includes[#script.includes + 1] = { line = 8, path = "pledge.inc" }

-- ChangeModel.scr
-- timmy
-- sets a model's filename and skin if player has the key
-- parameters:
-- p0 The key to check for
-- p1 The file name of the ABC
-- p2 the filename of the DTX
script.labels["Init"] = function(ctx)
    -- CHANGEMODEL.scr:21
    if not ctx:hasKey("nKey") then -- CHANGEMODEL.scr:24-25
        do return ctx:exit("") end -- CHANGEMODEL.scr:26
    end -- CHANGEMODEL.scr:27
    ctx:state().g_hobject = ctx:objectOrNil("Prop0") -- CHANGEMODEL.scr:29
    ctx:self():setModelFilenames("model_name", "Model_skin") -- CHANGEMODEL.scr:30
    do return ctx:exit("") end -- CHANGEMODEL.scr:32
end

script.labels["Main"] = function(ctx)
    -- CHANGEMODEL.scr:35
    -- traceon
    -- Don't Forget to Delete this!
    ctx:getParam(0, "nKey") -- CHANGEMODEL.scr:41
    ctx:getParam(1, "Model_Name") -- CHANGEMODEL.scr:42
    ctx:getParam(2, "Model_Skin") -- CHANGEMODEL.scr:43
    -- Addtrigger Use, OnUse
    ctx:wait(1, 1, "Init") -- CHANGEMODEL.scr:45
    do return ctx:exit("") end -- CHANGEMODEL.scr:46
end

return script
