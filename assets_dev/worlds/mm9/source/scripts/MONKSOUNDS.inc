;--------------------------------------------------
;monksounds.inc
; timmy
; 10/30
; randomizes guard idle sounds.
;--------------------------------------------------

#include globals.inc

#number		innerRadius = nVolume
#number		outerRadius = 300
#number		Is_Playing = 0
#number		Is_Sleeping = 0
#number		bIsDripping = 0
#number		bSoundOn = 1

#number		nVolume = 80

;--------------------------------------------------
:OnPray
;--------------------------------------------------

if (Is_Playing==TRUE)
	exit
endif

GetRandomInt 1, 10, G_ntemp

if (g_ntemp==1)
	PlaySound Sounds\AnimSounds\Monk\Pray1.wav, DoNothing, innerRadius, outerRadius, FALSE, nVolume
	set Is_Playing, TRUE
	wait 1 2.2, OnStop
	exit
endif

if (g_ntemp==2)
	PlaySound Sounds\AnimSounds\Monk\Pray2.wav, DoNothing, innerRadius, outerRadius, FALSE, nVolume
	set Is_Playing, TRUE
	wait 1 2.2, OnStop
	exit
endif

if (g_ntemp==3)
	PlaySound Sounds\AnimSounds\Monk\Pray3.wav, DoNothing, innerRadius, outerRadius, FALSE, nVolume
	set Is_Playing, TRUE
	wait 1 2.2, OnStop
	exit
endif

if (g_ntemp==4)
	PlaySound Sounds\AnimSounds\Monk\Pray4.wav, DoNothing, innerRadius, outerRadius, FALSE, nVolume
	set Is_Playing, TRUE
	wait 1 2.2, OnStop
	exit
endif



if (g_ntemp>4)

	Set Is_Playing, TRUE
	wait 1 20, ONStop
	exit
endif

exit

;--------------------------------------------------
:OnSweep
;--------------------------------------------------


if (Is_Sleeping==TRUE)
	exit
endif

	PlaySound Sounds\AnimSounds\Monk\Sweep.wav, DoNothing, innerRadius, outerRadius, FALSE, nVolume
	set Is_Sleeping, TRUE
	wait 1 1, OnStop
	exit



exit

;--------------------------------------------------
:OnWash
;--------------------------------------------------

if (bsoundOn==TRUE)

	PlaySound Sounds\AnimSounds\Monk\Wash.wav, DoNothing, innerRadius, outerRadius, FALSE, 10
endif
	
if (bIsDripping==TRUE)
	exit
endif

GetRandomInt 1, 10, G_ntemp
if (g_ntemp==1)
	PlaySound Sounds\AnimSounds\Monk\WashFidget.wav, DoNothing, innerRadius, outerRadius, FALSE, nVolume	
	set bIsDripping TRUE
	wait 1 5, OnStop
endif
exit

;--------------------------------------------------
:OnStop
;--------------------------------------------------

set Is_Playing, FALSE
set Is_Sleeping, FALSE
	set bIsDripping FALSE
exit

;--------------------------------------------------
:MS_Init
;--------------------------------------------------

;traceon
AddModelKey PrayMumble OnPray
AddModelKey Sweep, OnSweep
AddModelKey Wash, OnWash
exit

