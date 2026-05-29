-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DOORLOCK.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 10, path = "globals.inc" }

-- Doorlock.scr
-- timmy
-- handles locked door stuff
-- edited by Bones -- 6/10/03
-- TELP Patch 1.3 -- specified doors will re-lock
-- parameters
-- p0 item number of key
-- p1 whether to take the key after use
script.labels["OnUse"] = function(ctx)
    -- DOORLOCK.scr:22
    if ctx:hasItem("nKey") then -- DOORLOCK.scr:25-26
        ctx:self():setStat("Locked", "FALSE") -- DOORLOCK.scr:28
        ctx:rolloverText(17, 1) -- DOORLOCK.scr:29
        -- jsl	trigger g_hmyobject Unlock
        -- jsl	trigger g_hmyobject use
        if ctx:condition("bTakeKey==TRUE") then -- DOORLOCK.scr:33
            ctx:takeItem("nKey") -- DOORLOCK.scr:34
        end -- DOORLOCK.scr:35
        if ctx:condition("bLockDoor==TRUE") then -- DOORLOCK.scr:37
            ctx:self():setStat("Locked", "TRUE") -- DOORLOCK.scr:38
            -- jsl		trigger g_hmyobject Lock
        end -- DOORLOCK.scr:42
        do return ctx:exit("FALSE") end -- DOORLOCK.scr:44
    end -- DOORLOCK.scr:46
    do return ctx:exit("FALSE") end -- DOORLOCK.scr:48
end

script.labels["Main"] = function(ctx)
    -- DOORLOCK.scr:52
    -- traceon
    -- Don't Forget to Delete this!
    ctx:addTrigger("use", "OnUse") -- DOORLOCK.scr:57
    ctx:getParam(0, "nKey") -- DOORLOCK.scr:58
    ctx:getParam(1, "bTakeKey") -- DOORLOCK.scr:59
    ctx:getParam(2, "bLockDoor") -- DOORLOCK.scr:60
    do return ctx:exit("") end -- DOORLOCK.scr:62
end

return script
