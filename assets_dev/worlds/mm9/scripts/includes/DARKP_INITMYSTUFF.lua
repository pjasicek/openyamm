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
    ctx:arrayPut("aBridges", 0, 0) -- DARKP_INITMYSTUFF.inc:24
    ctx:arrayPut("aBridges", 1, 1) -- DARKP_INITMYSTUFF.inc:25
    ctx:arrayPut("aBridges", 2, 1) -- DARKP_INITMYSTUFF.inc:26
    ctx:arrayPut("aBridges", 3, 1) -- DARKP_INITMYSTUFF.inc:27
    ctx:arrayPut("aBridges", 4, 0) -- DARKP_INITMYSTUFF.inc:28
    ctx:arrayPut("aA", 0, 0) -- DARKP_INITMYSTUFF.inc:30
    ctx:arrayPut("aA", 1, 5) -- DARKP_INITMYSTUFF.inc:31
    ctx:arrayPut("aA", 5, 14) -- DARKP_INITMYSTUFF.inc:32
    ctx:arrayPut("aA", 9, 21) -- DARKP_INITMYSTUFF.inc:33
    ctx:arrayPut("aA", 14, 22) -- DARKP_INITMYSTUFF.inc:34
    ctx:arrayPut("aA", 17, 0) -- DARKP_INITMYSTUFF.inc:35
    ctx:arrayPut("aA", 19, 22) -- DARKP_INITMYSTUFF.inc:36
    ctx:arrayPut("aA", 21, 14) -- DARKP_INITMYSTUFF.inc:37
    ctx:arrayPut("aA", 22, 14) -- DARKP_INITMYSTUFF.inc:38
    ctx:arrayPut("aA", 23, 14) -- DARKP_INITMYSTUFF.inc:39
    ctx:arrayPut("aA", 25, 9) -- DARKP_INITMYSTUFF.inc:40
    ctx:arrayPut("aA", 26, 5) -- DARKP_INITMYSTUFF.inc:41
    ctx:arrayPut("aA", 29, 1) -- DARKP_INITMYSTUFF.inc:42
    ctx:arrayPut("aA", 30, 1) -- DARKP_INITMYSTUFF.inc:43
    ctx:arrayPut("aA", 31, 9) -- DARKP_INITMYSTUFF.inc:44
    ctx:arrayPut("aB", 0, 0) -- DARKP_INITMYSTUFF.inc:46
    ctx:arrayPut("aB", 1, 9) -- DARKP_INITMYSTUFF.inc:47
    ctx:arrayPut("aB", 5, 30) -- DARKP_INITMYSTUFF.inc:48
    ctx:arrayPut("aB", 9, 23) -- DARKP_INITMYSTUFF.inc:49
    ctx:arrayPut("aB", 14, 5) -- DARKP_INITMYSTUFF.inc:50
    ctx:arrayPut("aB", 17, 9) -- DARKP_INITMYSTUFF.inc:51
    ctx:arrayPut("aB", 19, 31) -- DARKP_INITMYSTUFF.inc:52
    ctx:arrayPut("aB", 21, 5) -- DARKP_INITMYSTUFF.inc:53
    ctx:arrayPut("aB", 22, 1) -- DARKP_INITMYSTUFF.inc:54
    ctx:arrayPut("aB", 23, 1) -- DARKP_INITMYSTUFF.inc:55
    ctx:arrayPut("aB", 25, 17) -- DARKP_INITMYSTUFF.inc:56
    ctx:arrayPut("aB", 26, 23) -- DARKP_INITMYSTUFF.inc:57
    ctx:arrayPut("aB", 29, 23) -- DARKP_INITMYSTUFF.inc:58
    ctx:arrayPut("aB", 30, 9) -- DARKP_INITMYSTUFF.inc:59
    ctx:arrayPut("aB", 31, 23) -- DARKP_INITMYSTUFF.inc:60
    ctx:arrayPut("aC", 0, 0) -- DARKP_INITMYSTUFF.inc:62
    ctx:arrayPut("aC", 1, 23) -- DARKP_INITMYSTUFF.inc:63
    ctx:arrayPut("aC", 5, 1) -- DARKP_INITMYSTUFF.inc:64
    ctx:arrayPut("aC", 9, 22) -- DARKP_INITMYSTUFF.inc:65
    ctx:arrayPut("aC", 14, 23) -- DARKP_INITMYSTUFF.inc:66
    ctx:arrayPut("aC", 17, 5) -- DARKP_INITMYSTUFF.inc:67
    ctx:arrayPut("aC", 19, 23) -- DARKP_INITMYSTUFF.inc:68
    ctx:arrayPut("aC", 21, 19) -- DARKP_INITMYSTUFF.inc:69
    ctx:arrayPut("aC", 22, 30) -- DARKP_INITMYSTUFF.inc:70
    ctx:arrayPut("aC", 23, 9) -- DARKP_INITMYSTUFF.inc:71
    ctx:arrayPut("aC", 25, 5) -- DARKP_INITMYSTUFF.inc:72
    ctx:arrayPut("aC", 26, 31) -- DARKP_INITMYSTUFF.inc:73
    ctx:arrayPut("aC", 29, 25) -- DARKP_INITMYSTUFF.inc:74
    ctx:arrayPut("aC", 30, 5) -- DARKP_INITMYSTUFF.inc:75
    ctx:arrayPut("aC", 31, 21) -- DARKP_INITMYSTUFF.inc:76
    ctx:arrayPut("aD", 0, 0) -- DARKP_INITMYSTUFF.inc:78
    ctx:arrayPut("aD", 1, 30) -- DARKP_INITMYSTUFF.inc:79
    ctx:arrayPut("aD", 5, 22) -- DARKP_INITMYSTUFF.inc:80
    ctx:arrayPut("aD", 9, 26) -- DARKP_INITMYSTUFF.inc:81
    ctx:arrayPut("aD", 14, 30) -- DARKP_INITMYSTUFF.inc:82
    ctx:arrayPut("aD", 17, 23) -- DARKP_INITMYSTUFF.inc:83
    ctx:arrayPut("aD", 19, 30) -- DARKP_INITMYSTUFF.inc:84
    ctx:arrayPut("aD", 21, 9) -- DARKP_INITMYSTUFF.inc:85
    ctx:arrayPut("aD", 22, 21) -- DARKP_INITMYSTUFF.inc:86
    ctx:arrayPut("aD", 23, 22) -- DARKP_INITMYSTUFF.inc:87
    ctx:arrayPut("aD", 25, 23) -- DARKP_INITMYSTUFF.inc:88
    ctx:arrayPut("aD", 26, 9) -- DARKP_INITMYSTUFF.inc:89
    ctx:arrayPut("aD", 29, 30) -- DARKP_INITMYSTUFF.inc:90
    ctx:arrayPut("aD", 30, 23) -- DARKP_INITMYSTUFF.inc:91
    ctx:arrayPut("aD", 31, 29) -- DARKP_INITMYSTUFF.inc:92
    do return ctx:exit(1) end -- DARKP_INITMYSTUFF.inc:94
end

return script
