-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "IS_BOAT.scr"
script.includes = {}
script.labels = {}

script.includes[#script.includes + 1] = { line = 15, path = "globals.inc" }

-- Capstone.scr
-- By Timmy
-- gives the player the Capstone of Order
-- and the related key
-- Igrid's RudeID is 338
-- capstone is item 396
-- NOTE:  The final quest has changed, so you don't need to get
-- the capstone a second time to lure Njam into tomb
-- flag variables
script.labels["OnMove"] = function(ctx)
    -- IS_BOAT.scr:34
    ctx:command("getmyhandle", "g_hMyobject") -- IS_BOAT.scr:37
    ctx:command("setflag", "g_hmyobject, visible") -- IS_BOAT.scr:38
    ctx:command("getpos", "g_hMyobject MyX MyY MyZ") -- IS_BOAT.scr:39
    ctx:command("getobjecthandle", "BoatMarker g_hobject") -- IS_BOAT.scr:40
    ctx:command("getpos", "g_hobject Xpos Ypos Zpos") -- IS_BOAT.scr:41
    ctx:command("movetopos", "xpos MyY Zpos 100 DoNothing") -- IS_BOAT.scr:42
    do return ctx:exit("") end -- IS_BOAT.scr:44
end

script.labels["placed2"] = function(ctx)
    -- IS_BOAT.scr:46
    ctx:command("getmyhandle", "g_hmyobject") -- IS_BOAT.scr:49
    ctx:command("clearflag", "g_hmyobject, visible") -- IS_BOAT.scr:50
    do return ctx:exit("") end -- IS_BOAT.scr:51
end

script.labels["Main"] = function(ctx)
    -- IS_BOAT.scr:56
    -- TraceOn ;DELETE ME!!
    ctx:addTrigger("Move", "OnMove") -- IS_BOAT.scr:62
    mm9.gosub(script, ctx, "placed2") -- IS_BOAT.scr:64
    do return ctx:exit("") end -- IS_BOAT.scr:65
end

return script
