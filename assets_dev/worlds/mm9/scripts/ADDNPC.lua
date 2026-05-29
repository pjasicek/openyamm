-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "ADDNPC.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 7, path = "globals.inc" }

-- AddNPC.scr
-- timmy
-- handles Aymril Banito voice and quest stuff
script.labels["ONUse"] = function(ctx)
    -- ADDNPC.scr:17
    if ctx:condition("nKeycheck==false") then -- ADDNPC.scr:19
        ctx:addNpc(2, "g_hobject") -- ADDNPC.scr:20
        ctx:state().nKeycheck = true -- ADDNPC.scr:21
    else -- ADDNPC.scr:22
        ctx:removeNpc(2, "g_hobject") -- ADDNPC.scr:23
        ctx:state().nKeycheck = false -- ADDNPC.scr:24
    end -- ADDNPC.scr:25
    do return ctx:exit("") end -- ADDNPC.scr:26
end

script.labels["Main"] = function(ctx)
    -- ADDNPC.scr:29
    ctx:traceOn() -- ADDNPC.scr:32
    -- Don't Forget to Delete this!
    ctx:addTrigger("Use", "OnUse") -- ADDNPC.scr:34
    do return ctx:exit("") end -- ADDNPC.scr:35
end

return script
