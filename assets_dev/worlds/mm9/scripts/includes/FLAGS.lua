-- generated from MM9 script source; do not edit by hand
local mm9 = mm9ScriptRuntime
local script = {}
script.source = "FLAGS.inc"
script.includes = {}
script.labels = {}


-- FLAGS.INC
-- This include file contains script equivalents to
-- engine flags....
-- Is this model visible?
-- Does this model cast shadows?
-- For lights only..
-- For Models only..
-- Use the 'fastlight' method for this light.
-- Environment map the model.
-- Object can't go thru other solid objects.
-- Use simple box physics on this object (used for WorldModels and containers).
-- Gets touch notification.
-- Gravity is applied.
-- The object won't get get MID_MODELSTRINGKEY messages unless
-- Object can pass through world
return script
