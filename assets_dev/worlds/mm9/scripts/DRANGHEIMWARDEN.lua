-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DRANGHEIMWARDEN.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseGlobals.inc" }
script.includes[#script.includes + 1] = { line = 10, path = "BaseMelee.inc" }
script.includes[#script.includes + 1] = { line = 11, path = "DrangheimHostility.inc" }

-- DrangheimWarden.scr
-- SJR
-- Feltup by kd 10-30-01
-- This guard operates the levels that open
-- and close the cell doors.
script.labels["Main"] = function(ctx)
    -- DRANGHEIMWARDEN.scr:22
    ctx:getParam(0, "sCellName") -- DRANGHEIMWARDEN.scr:24
    ctx:arrayPut("spCellNames", 0, "sCellName") -- DRANGHEIMWARDEN.scr:25
    ctx:getParam(1, "sCellName") -- DRANGHEIMWARDEN.scr:26
    ctx:arrayPut("spCellNames", 1, "sCellName") -- DRANGHEIMWARDEN.scr:27
    ctx:getParam(2, "sCellName") -- DRANGHEIMWARDEN.scr:28
    ctx:arrayPut("spCellNames", 2, "sCellName") -- DRANGHEIMWARDEN.scr:29
    mm9.gosub(script, ctx, "InitDrangheimHostility") -- DRANGHEIMWARDEN.scr:31
    ctx:addTrigger("open", "OpenCell") -- DRANGHEIMWARDEN.scr:33
    ctx:addTrigger("close", "CloseCell") -- DRANGHEIMWARDEN.scr:34
    ctx:addTrigger("change", "ChangeCell") -- DRANGHEIMWARDEN.scr:35
    ctx:state().nCounter = 0 -- DRANGHEIMWARDEN.scr:37
    do return ctx:exit("TRUE") end -- DRANGHEIMWARDEN.scr:39
end

script.labels["OpenCell"] = function(ctx)
    -- DRANGHEIMWARDEN.scr:42
    ctx:self():playAnimation("aware", "DoNothing") -- DRANGHEIMWARDEN.scr:44
    if ctx:condition("hCell!=0") then -- DRANGHEIMWARDEN.scr:45
        ctx:trigger("hCell", "use") -- DRANGHEIMWARDEN.scr:46
    end -- DRANGHEIMWARDEN.scr:47
    do return ctx:exit("TRUE") end -- DRANGHEIMWARDEN.scr:49
end

script.labels["CloseCell"] = function(ctx)
    -- DRANGHEIMWARDEN.scr:52
    ctx:self():playAnimation("aware", "DoNothing") -- DRANGHEIMWARDEN.scr:54
    if ctx:condition("hCell!=0") then -- DRANGHEIMWARDEN.scr:55
        ctx:trigger("hCell", "use") -- DRANGHEIMWARDEN.scr:56
    end -- DRANGHEIMWARDEN.scr:57
    do return ctx:exit("TRUE") end -- DRANGHEIMWARDEN.scr:59
end

script.labels["ChangeCell"] = function(ctx)
    -- DRANGHEIMWARDEN.scr:62
    ctx:arrayGet("spCellNames", "nCounter", "sCellName") -- DRANGHEIMWARDEN.scr:64
    ctx:state().hCell = ctx:objectOrNil("sCellName") -- DRANGHEIMWARDEN.scr:65
    ctx:set("nCounter", "nCounter + 1") -- DRANGHEIMWARDEN.scr:66
    ctx:mod("nCounter", 3) -- DRANGHEIMWARDEN.scr:67
    do return ctx:exit("TRUE") end -- DRANGHEIMWARDEN.scr:69
end

return script
