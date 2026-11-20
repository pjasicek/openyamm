artifactPower={}

-- Converted from the old artifactStatsBonus/artifactSkillBonus numbers by
-- keeping each artifact's INTERNAL split and renormalising its upside to 3.
-- A skill point was priced at 10 stat points, which is the ratio the old
-- tables used. Drawbacks kept the same exchange rate as the upside they sit
-- next to, so an artifact that gave up a lot still gives it up.

-- Ogre's Hammer
artifactPower[500] = {	[const.Stats.Accuracy] = 3}
-- Sword of Might
artifactPower[501] = {	[const.Stats.Might] = 3}
artifactPower[502] = {	[const.Stats.AirResistance] = 1.76,
						Skills = {	[const.Skills.Armsmaster] = 1.24}}
artifactPower[503] = {	[const.Stats.Endurance] = 1.5,
						[const.Stats.Luck] = 1.5}
artifactPower[504] = {	[const.Stats.Might] = 3}
artifactPower[505] = {	[const.Stats.FireResistance] = 3}
artifactPower[506] = {	[const.Stats.Endurance] = 3}
artifactPower[507] = {	[const.Stats.Might] 		= 0.43,
						[const.Stats.Intellect] 	= 0.43,
						[const.Stats.Personality] 	= 0.43,
						[const.Stats.Speed] 		= 0.43,
						[const.Stats.Accuracy]		= 0.43,
						[const.Stats.Endurance] 	= 0.43,
						[const.Stats.Luck]			= 0.43}
artifactPower[509] = {	[const.Stats.Personality] = 3}
artifactPower[510] = {	[const.Stats.Might] = 1.5,
						[const.Stats.Endurance] = 1.5}
artifactPower[512] = {	[const.Stats.Accuracy] = 1.67,
						Skills = {	[const.Skills.Bow] = 1.33}}
artifactPower[513] = {	[const.Stats.Endurance] = 3}
artifactPower[514] = {	[const.Stats.Might] 		= 0.23,
						[const.Stats.Intellect] 	= 0.23,
						[const.Stats.Personality] 	= 0.23,
						[const.Stats.Speed] 		= 0.23,
						[const.Stats.Accuracy]		= 0.23,
						[const.Stats.Endurance] 	= 0.23,
						[const.Stats.Luck]			= 0.23,
						[const.Stats.FireResistance]	= 0.23,
						[const.Stats.AirResistance]		= 0.23,
						[const.Stats.WaterResistance]	= 0.23,
						[const.Stats.EarthResistance]	= 0.23,
						[const.Stats.MindResistance]	= 0.23,
						[const.Stats.BodyResistance]	= 0.23}
artifactPower[515] = {	[const.Stats.Speed] = 1.5,
						[const.Stats.Accuracy] = 1.5}
artifactPower[517] = {	Skills = {	[const.Skills.DisarmTraps] = 1,
									[const.Skills.Bow] = 1,
									[const.Skills.Armsmaster] = 1}}
artifactPower[518] = {	[const.Stats.Speed] = 3}
artifactPower[519] = {	[const.Stats.FireResistance]	= 0.75,
						[const.Stats.AirResistance]		= 0.75,
						[const.Stats.WaterResistance]	= 0.75,
						[const.Stats.EarthResistance]	= 0.75}
artifactPower[520] = {	[const.Stats.Personality] = 1.5,
						[const.Stats.Intellect] = 1.5}
artifactPower[521] = {	[const.Stats.Intellect] = 3}
artifactPower[522] = {	[const.Stats.Intellect] = 1.2,
						[const.Stats.FireResistance]	= 0.3,
						[const.Stats.AirResistance]		= 0.3,
						[const.Stats.WaterResistance]	= 0.3,
						[const.Stats.EarthResistance]	= 0.3,
						[const.Stats.MindResistance]	= 0.3,
						[const.Stats.BodyResistance]	= 0.3}
artifactPower[523] = {	[const.Stats.Speed] = 3,
						[const.Stats.WaterResistance] = -1.5,
						[const.Stats.Personality] = -0.45}
artifactPower[524] = {	[const.Stats.Speed] = 1.5,
						[const.Stats.Accuracy] = 1.5,
						[const.Stats.ArmorClass] = -0.43}
artifactPower[525] = {	[const.Stats.Accuracy] = 3,
						[const.Stats.Speed] = -0.5}
artifactPower[526] = {	[const.Stats.Might] = 1.5,
						[const.Stats.Accuracy] = 1.5,
						[const.Stats.Personality] = -1.07,
						[const.Stats.Intellect] = -1.07}
artifactPower[527] = {	[const.Stats.Might] = 3,
						[const.Stats.Luck] = -1.5}
artifactPower[528] = {	[const.Stats.WaterResistance] = 3,
						[const.Stats.FireResistance] = -0.86}
artifactPower[529] = {	[const.Stats.Might] = 1.5,
						[const.Stats.Accuracy] = 1.5}
-- Staff of Elements: its four spell schools are the item, the AC is the price
artifactPower[530] = {	[const.Stats.ArmorClass] = -1.2}
artifactPower[531] = {	[const.Stats.Accuracy] = 2.14,
						[const.Stats.ArmorClass] = -0.43,
						Skills = {	[const.Skills.Bow] = 0.86}}
artifactPower[532] = {	[const.Stats.Might] = 1.5,
						[const.Stats.Speed] = 1.5}
artifactPower[533] = {	[const.Stats.Intellect] = 1.5,
						[const.Stats.Personality] = 1.5,
						[const.Stats.MindResistance] = -1.07,
						[const.Stats.BodyResistance] = -1.07}
artifactPower[534] = {	[const.Stats.Endurance] = 3,
						[const.Stats.Luck] = -0.9}
artifactPower[535] = {	[const.Stats.Intellect] = 1.64,
						[const.Stats.Endurance] = -0.55,
						Skills = {	[const.Skills.Alchemy] = 1.36}}
artifactPower[536] = {	[const.Stats.Luck] = 3,
						[const.Stats.Personality] = -1.5}
artifactPower[537] = {	[const.Stats.Might] = 3,
						[const.Stats.Accuracy] = -0.75,
						[const.Stats.ArmorClass] = -0.38}
-- Cycle of life
artifactPower[543] = {	[const.Stats.Endurance] = 3}

-- Puck
artifactPower[1302] = {	[const.Stats.Speed] = 3}
-- Iron Feather
artifactPower[1303] = {	[const.Stats.Might] = 3}
-- Wallace
artifactPower[1304] = {	[const.Stats.Personality] = 0.86,
						Skills = {	[const.Skills.Armsmaster] = 2.14}}
-- Corsair
artifactPower[1305] = {	[const.Stats.Luck] = 1.33,
						Skills = {	[const.Skills.DisarmTraps] = 1.67}}
-- Governor's Armor
artifactPower[1306] = {	[const.Stats.Might] 		= 0.43,
						[const.Stats.Intellect] 	= 0.43,
						[const.Stats.Personality] 	= 0.43,
						[const.Stats.Speed] 		= 0.43,
						[const.Stats.Accuracy]		= 0.43,
						[const.Stats.Endurance] 	= 0.43,
						[const.Stats.Luck]			= 0.43}
-- Yoruba
artifactPower[1307] = {	[const.Stats.Endurance] = 3}
-- Splitter: fire immunity is a threshold, not a budget -- see Flat
artifactPower[1308] = {	Flat = {	[const.Stats.FireResistance] = 65000}}
-- Ullyses
artifactPower[1312] = {	[const.Stats.Accuracy] = 3}
-- Hands of the Master
artifactPower[1313] = {	Skills = {	[const.Skills.Unarmed] = 1.5,
									[const.Skills.Dodging] = 1.5}}
-- Seven League Boots
artifactPower[1314] = {	[const.Stats.Speed] = 3}
-- Mash
artifactPower[1316] = {	[const.Stats.Might] = 3,
						[const.Stats.Intellect] = -0.8,
						[const.Stats.Personality] = -0.8,
						[const.Stats.Speed] = -0.8}
-- Ethric's Staff
artifactPower[1317] = {	Skills = {	[const.Skills.Meditation] = 3}}
-- Hareck's Leather
artifactPower[1318] = {	[const.Stats.Luck] = 1.5,
						[const.Stats.FireResistance] 	= -0.3,
						[const.Stats.AirResistance] 	= -0.3,
						[const.Stats.WaterResistance] 	= -0.3,
						[const.Stats.EarthResistance] 	= -0.3,
						[const.Stats.MindResistance] 	= -0.3,
						[const.Stats.BodyResistance] 	= -0.3,
						Skills = {	[const.Skills.Dagger] = 0.75,
									[const.Skills.Unarmed] = 0.75}}
-- Old Nick
artifactPower[1319] = {	Skills = {	[const.Skills.DisarmTraps] = 3}}
-- Amuck
artifactPower[1320] = {	[const.Stats.Might] = 1.5,
						[const.Stats.Endurance] = 1.5,
						[const.Stats.ArmorClass] = -0.23}
-- Glory shield
artifactPower[1321] = {	[const.Stats.BodyResistance] = -1.2,
						[const.Stats.MindResistance] = -1.2,
						Skills = {	[const.Skills.Shield] = 3}}
-- Kelebrim
artifactPower[1322] = {	[const.Stats.Endurance] = 3,
						[const.Stats.EarthResistance] = -1.8}
-- Taledon's Helm
artifactPower[1323] = {	[const.Stats.Might] = 1.5,
						[const.Stats.Personality] = 1.5,
						[const.Stats.Luck] = -1.33}
-- Scholar's Cap
artifactPower[1324] = {	[const.Stats.Endurance] = -1,
						Skills = {	[const.Skills.Learning] = 3}}
-- Phynaxian Crown
artifactPower[1325] = {	[const.Stats.Personality] = 0.69,
						[const.Stats.WaterResistance] = 2.31,
						[const.Stats.ArmorClass] = -0.46}
-- Titan's Belt
artifactPower[1326] = {	[const.Stats.Might] = 3,
						[const.Stats.Speed] = -1.04}
-- Twilight
artifactPower[1327] = {	[const.Stats.Speed] = 1.5,
						[const.Stats.Luck] = 1.5,
						[const.Stats.FireResistance] = -0.9,
						[const.Stats.AirResistance] = -0.9,
						[const.Stats.WaterResistance] = -0.9,
						[const.Stats.EarthResistance] = -0.9,
						[const.Stats.MindResistance] = -0.9,
						[const.Stats.BodyResistance] = -0.9}
-- Ania Selving
artifactPower[1328] = {	[const.Stats.Accuracy] = 2.25,
						[const.Stats.ArmorClass] = -0.38,
						Skills = {	[const.Skills.Bow] = 0.75}}
-- Justice
artifactPower[1329] = {	[const.Stats.Speed] = -1.2}
-- Mekorig's hammer
artifactPower[1330] = {	[const.Stats.Might] = 3,
						[const.Stats.AirResistance] = -4}
-- Hermes's Sandals
artifactPower[1331] = {	[const.Stats.Speed] = 1.2,
						[const.Stats.Accuracy] = 0.6,
						[const.Stats.AirResistance] = 1.2}
-- Cloak of the sheep
artifactPower[1332] = {	[const.Stats.Intellect] = -0.6,
						[const.Stats.Personality] = -0.6}
-- Elfbane
artifactPower[1333] = {	[const.Stats.Speed] = 3}
-- Mind's Eye
artifactPower[1334] = {	[const.Stats.Intellect] = 1.5,
						[const.Stats.Personality] = 1.5}
-- Elven Chainmail
artifactPower[1335] = {	[const.Stats.Speed] = 1.5,
						[const.Stats.Accuracy] = 1.5}
-- Forge Gauntlets
artifactPower[1336] = {	[const.Stats.Might] = 0.75,
						[const.Stats.Endurance] = 0.75,
						[const.Stats.FireResistance] = 1.5}
-- Hero's belt
artifactPower[1337] = {	[const.Stats.Might] = 1.13,
						Skills = {	[const.Skills.Armsmaster] = 1.88}}
-- Lady's Escort ring
artifactPower[1338] = {	[const.Stats.FireResistance]	= 0.5,
						[const.Stats.AirResistance]		= 0.5,
						[const.Stats.WaterResistance]	= 0.5,
						[const.Stats.EarthResistance]	= 0.5,
						[const.Stats.MindResistance]	= 0.5,
						[const.Stats.BodyResistance]	= 0.5}
-- Thor
artifactPower[2021] = {	[const.Stats.Might] = 3}
-- Conan
artifactPower[2022] = {	[const.Stats.Accuracy] = 3}
-- Excalibur
artifactPower[2023] = {	[const.Stats.Might] = 3}
-- Merlin
artifactPower[2024] = {	[const.Stats.Intellect] = 0.82,
						[const.Stats.Personality] = 0.82,
						[const.Stats.SP] = 1.36}
-- Percival
artifactPower[2025] = {	[const.Stats.Speed] = 3}
-- Galahad
artifactPower[2026] = {	[const.Stats.Endurance] = 3}
-- Pellinore
artifactPower[2027] = {	[const.Stats.Endurance] = 3}
-- Valeria
artifactPower[2028] = {	[const.Stats.Accuracy] = 3}
-- Arthur
artifactPower[2029] = {	[const.Stats.Might] = 0.25,
						[const.Stats.Intellect] = 0.25,
						[const.Stats.Personality] = 0.25,
						[const.Stats.Endurance] = 0.25,
						[const.Stats.Accuracy] = 0.25,
						[const.Stats.Speed] = 0.25,
						[const.Stats.Luck] = 0.25,
						[const.Stats.SP] = 1.25}
-- Pendragon
artifactPower[2030] = {	[const.Stats.Luck] = 0.86,
						Skills = {	[const.Skills.Dagger] = 0.71,
									[const.Skills.DisarmTraps] = 1.43}}
-- Lucius
artifactPower[2031] = {	[const.Stats.Speed] = 3}
-- Guinevere
artifactPower[2032] = {	[const.Stats.SP] = 3}
-- Igraine
artifactPower[2033] = {	[const.Stats.SP] = 3}
-- Morgan
artifactPower[2034] = {	[const.Stats.SP] = 3}
-- Hades
artifactPower[2035] = {	[const.Stats.Luck] = 1.13,
						Skills = {	[const.Skills.DisarmTraps] = 1.88}}
-- Ares
artifactPower[2036] = {	[const.Stats.FireResistance] = 3}
-- Poseidon
artifactPower[2037] = {	[const.Stats.Might] = 1,
						[const.Stats.Endurance] = 1,
						[const.Stats.Accuracy] = 1,
						[const.Stats.Speed] = -0.25,
						[const.Stats.ArmorClass] = -0.25}
-- Cronos
artifactPower[2038] = {	[const.Stats.Endurance] = 3,
						[const.Stats.Luck] = -1.5}
-- Hercules
artifactPower[2039] = {	[const.Stats.Might] = 1.88,
						[const.Stats.Endurance] = 1.13,
						[const.Stats.Intellect] = -0.56}
-- Artemis
artifactPower[2040] = {	[const.Stats.FireResistance] = -0.6,
						[const.Stats.AirResistance] = -0.6,
						[const.Stats.WaterResistance] = -0.6,
						[const.Stats.EarthResistance] = -0.6}
-- Apollo
artifactPower[2041] = {	[const.Stats.FireResistance] = 0.46,
						[const.Stats.AirResistance] = 0.46,
						[const.Stats.WaterResistance] = 0.46,
						[const.Stats.EarthResistance] = 0.46,
						[const.Stats.MindResistance] = 0.46,
						[const.Stats.BodyResistance] = 0.46,
						[const.Stats.Luck] = 0.23,
						[const.Stats.Endurance] = -0.35}
-- Zeus
artifactPower[2042] = {	[const.Stats.Endurance] = 1,
						[const.Stats.Personality] = 1,
						[const.Stats.Luck] = 1,
						[const.Stats.Intellect] = -1}
-- Aegis
artifactPower[2043] = {	[const.Stats.Luck] = 3,
						[const.Stats.Speed] = -0.6}
-- Odin
artifactPower[2044] = {	[const.Stats.FireResistance] = 0.75,
						[const.Stats.AirResistance] = 0.75,
						[const.Stats.WaterResistance] = 0.75,
						[const.Stats.EarthResistance] = 0.75,
						[const.Stats.Speed] = -0.5}
-- Atlas
artifactPower[2045] = {	[const.Stats.Might] = 3,
						[const.Stats.Speed] = -1}
-- Hermes
artifactPower[2046] = {	[const.Stats.Speed] = 3,
						[const.Stats.Accuracy] = -0.86}
-- Aphrodite
artifactPower[2047] = {	[const.Stats.Personality] = 3,
						[const.Stats.Luck] = -1.2}
-- Athena
artifactPower[2048] = {	[const.Stats.Intellect] = 3,
						[const.Stats.Might] = -1.2}
-- Hera
artifactPower[2049] = {	[const.Stats.HP] = 1.2,
						[const.Stats.SP] = 1.2,
						[const.Stats.Luck] = 0.6,
						[const.Stats.Personality] = -0.6}
