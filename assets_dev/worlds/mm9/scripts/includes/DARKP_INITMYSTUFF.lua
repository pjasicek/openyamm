-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "DARKP_INITMYSTUFF.inc"
script.includes = {}
script.labels = {}


-- DarkP_initMyStuff.inc
-- Brett Yagi
-- 11/09/2001
-- Initialization file for DarkP_bridgepuzzle.scr
-- Sequence to completion - ADCBDCBA
script.labels["InitializeStuff"] = function(ctx)
    -- DARKP_INITMYSTUFF.inc:21
    ctx:command("arrayput", "aBridges 0 0") -- DARKP_INITMYSTUFF.inc:24
    ctx:command("arrayput", "aBridges 1 1") -- DARKP_INITMYSTUFF.inc:25
    ctx:command("arrayput", "aBridges 2 1") -- DARKP_INITMYSTUFF.inc:26
    ctx:command("arrayput", "aBridges 3 1") -- DARKP_INITMYSTUFF.inc:27
    ctx:command("arrayput", "aBridges 4 0") -- DARKP_INITMYSTUFF.inc:28
    ctx:command("arrayput", "aA  0 0") -- DARKP_INITMYSTUFF.inc:30
    ctx:command("arrayput", "aA  1 5") -- DARKP_INITMYSTUFF.inc:31
    ctx:command("arrayput", "aA  5 14") -- DARKP_INITMYSTUFF.inc:32
    ctx:command("arrayput", "aA  9 21") -- DARKP_INITMYSTUFF.inc:33
    ctx:command("arrayput", "aA 14 22") -- DARKP_INITMYSTUFF.inc:34
    ctx:command("arrayput", "aA 17 0") -- DARKP_INITMYSTUFF.inc:35
    ctx:command("arrayput", "aA 19 22") -- DARKP_INITMYSTUFF.inc:36
    ctx:command("arrayput", "aA 21 14") -- DARKP_INITMYSTUFF.inc:37
    ctx:command("arrayput", "aA 22 14") -- DARKP_INITMYSTUFF.inc:38
    ctx:command("arrayput", "aA 23 14") -- DARKP_INITMYSTUFF.inc:39
    ctx:command("arrayput", "aA 25 9") -- DARKP_INITMYSTUFF.inc:40
    ctx:command("arrayput", "aA 26 5") -- DARKP_INITMYSTUFF.inc:41
    ctx:command("arrayput", "aA 29 1") -- DARKP_INITMYSTUFF.inc:42
    ctx:command("arrayput", "aA 30 1") -- DARKP_INITMYSTUFF.inc:43
    ctx:command("arrayput", "aA 31 9") -- DARKP_INITMYSTUFF.inc:44
    ctx:command("arrayput", "aB  0 0") -- DARKP_INITMYSTUFF.inc:46
    ctx:command("arrayput", "aB  1 9") -- DARKP_INITMYSTUFF.inc:47
    ctx:command("arrayput", "aB  5 30") -- DARKP_INITMYSTUFF.inc:48
    ctx:command("arrayput", "aB  9 23") -- DARKP_INITMYSTUFF.inc:49
    ctx:command("arrayput", "aB 14 5") -- DARKP_INITMYSTUFF.inc:50
    ctx:command("arrayput", "aB 17 9") -- DARKP_INITMYSTUFF.inc:51
    ctx:command("arrayput", "aB 19 31") -- DARKP_INITMYSTUFF.inc:52
    ctx:command("arrayput", "aB 21 5") -- DARKP_INITMYSTUFF.inc:53
    ctx:command("arrayput", "aB 22 1") -- DARKP_INITMYSTUFF.inc:54
    ctx:command("arrayput", "aB 23 1") -- DARKP_INITMYSTUFF.inc:55
    ctx:command("arrayput", "aB 25 17") -- DARKP_INITMYSTUFF.inc:56
    ctx:command("arrayput", "aB 26 23") -- DARKP_INITMYSTUFF.inc:57
    ctx:command("arrayput", "aB 29 23") -- DARKP_INITMYSTUFF.inc:58
    ctx:command("arrayput", "aB 30 9") -- DARKP_INITMYSTUFF.inc:59
    ctx:command("arrayput", "aB 31 23") -- DARKP_INITMYSTUFF.inc:60
    ctx:command("arrayput", "aC  0 0") -- DARKP_INITMYSTUFF.inc:62
    ctx:command("arrayput", "aC  1 23") -- DARKP_INITMYSTUFF.inc:63
    ctx:command("arrayput", "aC  5 1") -- DARKP_INITMYSTUFF.inc:64
    ctx:command("arrayput", "aC  9 22") -- DARKP_INITMYSTUFF.inc:65
    ctx:command("arrayput", "aC 14 23") -- DARKP_INITMYSTUFF.inc:66
    ctx:command("arrayput", "aC 17 5") -- DARKP_INITMYSTUFF.inc:67
    ctx:command("arrayput", "aC 19 23") -- DARKP_INITMYSTUFF.inc:68
    ctx:command("arrayput", "aC 21 19") -- DARKP_INITMYSTUFF.inc:69
    ctx:command("arrayput", "aC 22 30") -- DARKP_INITMYSTUFF.inc:70
    ctx:command("arrayput", "aC 23 9") -- DARKP_INITMYSTUFF.inc:71
    ctx:command("arrayput", "aC 25 5") -- DARKP_INITMYSTUFF.inc:72
    ctx:command("arrayput", "aC 26 31") -- DARKP_INITMYSTUFF.inc:73
    ctx:command("arrayput", "aC 29 25") -- DARKP_INITMYSTUFF.inc:74
    ctx:command("arrayput", "aC 30 5") -- DARKP_INITMYSTUFF.inc:75
    ctx:command("arrayput", "aC 31 21") -- DARKP_INITMYSTUFF.inc:76
    ctx:command("arrayput", "aD  0 0") -- DARKP_INITMYSTUFF.inc:78
    ctx:command("arrayput", "aD  1 30") -- DARKP_INITMYSTUFF.inc:79
    ctx:command("arrayput", "aD  5 22") -- DARKP_INITMYSTUFF.inc:80
    ctx:command("arrayput", "aD  9 26") -- DARKP_INITMYSTUFF.inc:81
    ctx:command("arrayput", "aD 14 30") -- DARKP_INITMYSTUFF.inc:82
    ctx:command("arrayput", "aD 17 23") -- DARKP_INITMYSTUFF.inc:83
    ctx:command("arrayput", "aD 19 30") -- DARKP_INITMYSTUFF.inc:84
    ctx:command("arrayput", "aD 21 9") -- DARKP_INITMYSTUFF.inc:85
    ctx:command("arrayput", "aD 22 21") -- DARKP_INITMYSTUFF.inc:86
    ctx:command("arrayput", "aD 23 22") -- DARKP_INITMYSTUFF.inc:87
    ctx:command("arrayput", "aD 25 23") -- DARKP_INITMYSTUFF.inc:88
    ctx:command("arrayput", "aD 26 9") -- DARKP_INITMYSTUFF.inc:89
    ctx:command("arrayput", "aD 29 30") -- DARKP_INITMYSTUFF.inc:90
    ctx:command("arrayput", "aD 30 23") -- DARKP_INITMYSTUFF.inc:91
    ctx:command("arrayput", "aD 31 29") -- DARKP_INITMYSTUFF.inc:92
    do return ctx:exit(1) end -- DARKP_INITMYSTUFF.inc:94
end

return script
