-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IS_KILLINGLICH.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 9, path = "BaseMelee.inc" }

-- IS_KillingLich.scr
-- kd
-- 11-7-01
-- Makes the lich deal the killing blow to NPC
-- Adventure, then attack the party.
script.labels["Killem"] = function(ctx)
    -- IS_KILLINGLICH.scr:13
    ctx:trigger("hNpc", "Destroy") -- IS_KILLINGLICH.scr:15
    mm9.gosub(script, ctx, "BaseInit") -- IS_KILLINGLICH.scr:16
    do return ctx:exit("TRUE") end -- IS_KILLINGLICH.scr:17
end

script.labels["NpcDie"] = function(ctx)
    -- IS_KILLINGLICH.scr:19
    ctx:self():playAnimation("RAttack1", "Killem") -- IS_KILLINGLICH.scr:21
    do return ctx:exit("TRUE") end -- IS_KILLINGLICH.scr:22
end

script.labels["KillNpc"] = function(ctx)
    -- IS_KILLINGLICH.scr:24
    ctx:self():playAnimation("Fidget2", "NpcDie") -- IS_KILLINGLICH.scr:26
    do return ctx:exit("TRUE") end -- IS_KILLINGLICH.scr:27
end

script.labels["Main2"] = function(ctx)
    -- IS_KILLINGLICH.scr:29
    ctx:state().hNpc = ctx:objectOrNil("GreenPartyDude0") -- IS_KILLINGLICH.scr:31
    ctx:addTrigger("Kill", "KillNpc") -- IS_KILLINGLICH.scr:32
    do return ctx:exit("TRUE") end -- IS_KILLINGLICH.scr:33
end

script.labels["Main"] = function(ctx)
    -- IS_KILLINGLICH.scr:35
    ctx:wait(0, .1, "main2") -- IS_KILLINGLICH.scr:37
    do return ctx:exit("TRUE") end -- IS_KILLINGLICH.scr:38
end

return script
