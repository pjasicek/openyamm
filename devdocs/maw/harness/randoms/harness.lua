HERE=HERE or "/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/67306c2b-0ca8-4c66-afad-4546c9e2b3bb/scratchpad/randoms/"
-- harness: loads the verbatim MAW rarity code (extracted from zzMaw-Items.lua @ef23ee17)
vars = {}
mapvars = nil
Map = {Name="x"}
CURRENT_DIFF = 3
function GetDifficulty() return CURRENT_DIFF end
function round(x) return math.floor(x+0.5) end
dofile(HERE.."maw_rarity_extract.lua")
