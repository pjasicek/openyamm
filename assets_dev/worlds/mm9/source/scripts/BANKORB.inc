;--------------------------------------------------
;BankOrb.inc
; timmy
; handles Fiachna A'Lanth for the Orb of Linking
;
; edited by Bones 6/12/02
; TELP Patch 1.3 -- prevents Fiachna from taking extra orbs
;		(except for one extra at quest completion)
;--------------------------------------------------
#include globals.inc

#number		nKey
#String		sLocation

#number		nRude
#number		nKey2

; flag variables
#number							Visible = 1
#number							Solid   = 8192
#number							Gravity = 131072

;Parameters

;p0 the key to CheckFor when player placed the orb



;--------------------------------------------------
:OnRude
;--------------------------------------------------


haskey 330 g_ntemp
if (g_ntemp==TRUE)
	takekey 330
	haskey nKey g_ntemp
	if (g_ntemp==TRUE)
		Playsound sounds\events\quest.wav, DoNothing, 100, 24000, FALSE, 100
		takeitem 252
		givekey nKey2
		Gosub CheckAll
	endif
endif
exit


;--------------------------------------------------
:CheckAll
;--------------------------------------------------

haskey 337 g_ntemp
if (g_ntemp==TRUE)
	exit
endif

set g_ncounter, 0

haskey 331 g_ntemp
if (g_ntemp==TRUE)
	Add g_ncounter, 1
endif

haskey 332 g_ntemp
if (g_ntemp==TRUE)
	Add g_ncounter, 1
endif

haskey 333 g_ntemp
if (g_ntemp==TRUE)
	Add g_ncounter, 1
endif

haskey 334 g_ntemp
if (g_ntemp==TRUE)
	Add g_ncounter, 1
endif

haskey 335 g_ntemp
if (g_ntemp==TRUE)
	Add g_ncounter, 1
endif

haskey 336 g_ntemp
if (g_ntemp==TRUE)
	Add g_ncounter, 1
endif

if (g_ncounter==6)
	givekey 337
	giveexp 20000
	givegold 15000
	Playsound sounds\events\quest.wav, DoNothing, 100, 240, FALSE, 100
	takeitem 252
	exit
endif

exit

;--------------------------------------------------
:Init
;331	Player placed orb in Thronheim
;332	Player placed orb in guberland
;333	Player placed orb in frosgard
;334	Player placed orb in drangheim
;335	player placed orb in thjorgard
;336	player placed orb in sturmgard

;--------------------------------------------------


	set nKey 333
	set nKey2 327

exit

