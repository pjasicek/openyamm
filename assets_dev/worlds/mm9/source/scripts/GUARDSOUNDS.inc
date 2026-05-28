;--------------------------------------------------
;Guardsounds.inc
; timmy
; 10/30
; randomizes guard idle sounds.
;--------------------------------------------------

#include globals.inc

#number		innerRadius = 100
#number		outerRadius = 1000
#number		Is_Playing = 0
#number		Is_Sleeping = 0
         
;--------------------------------------------------
:OnStand
;--------------------------------------------------

if (Is_Playing==TRUE)
	exit
endif

GetRandomInt 1, 20, G_ntemp

if (g_ntemp==1)
	PlaySound Sounds\AnimSounds\Guard\Stand1.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Playing, TRUE
	wait 1 1.2, OnStop
	exit
endif

if (g_ntemp==2)
	PlaySound Sounds\AnimSounds\Guard\Stand2.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Playing, TRUE
	wait 1 1.2, OnStop
	exit
endif

if (g_ntemp==3)
	PlaySound Sounds\AnimSounds\Guard\Stand3.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Playing, TRUE
	wait 1 1.2, OnStop
	exit
endif

if (g_ntemp==4)
	PlaySound Sounds\AnimSounds\Guard\Stand4.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Playing, TRUE
	wait 1 1.2, OnStop
	exit
endif

if (g_ntemp==5)
	PlaySound Sounds\AnimSounds\Guard\Stand5.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Playing, TRUE
	wait 1 1.2, OnStop
	exit
endif

if (g_ntemp==6)
	PlaySound Sounds\AnimSounds\Guard\Stand6.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Playing, TRUE
	wait 1 1.2, OnStop
	exit
endif

if (g_ntemp==7)
	PlaySound Sounds\AnimSounds\Guard\Stand7.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Playing, TRUE
	wait 1 1.2, OnStop
	exit
endif

if (g_ntemp>7)

	Set Is_Playing, TRUE
	wait 1 50, ONStop
	exit
endif

exit

;--------------------------------------------------
:OnSleep
;--------------------------------------------------

if (Is_Sleeping==TRUE)
	exit
endif

GetRandomInt 1, 4, G_ntemp

if (g_ntemp==1)
	PlaySound Sounds\AnimSounds\Guard\Sleep1.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Sleeping, TRUE
	wait 1 5, OnStop
	exit
endif

if (g_ntemp==2)
	PlaySound Sounds\AnimSounds\Guard\Sleep2.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Sleeping, TRUE
	wait 1 5, OnStop
	exit
endif

if (g_ntemp==3)
	PlaySound Sounds\AnimSounds\Guard\Sleep3.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Sleeping, TRUE
	wait 1 5, OnStop
	exit
endif

if (g_ntemp==4)
	PlaySound Sounds\AnimSounds\Guard\Sleep4.wav, DoNothing, innerRadius, outerRadius, FALSE, 100
	set Is_Sleeping, TRUE
	wait 1 7, OnStop
	exit
endif

if (g_ntemp>4)
	Set Is_Sleeping, TRUE
	wait 1 10, ONStop
	exit
endif
exit

;--------------------------------------------------
:OnStop
;--------------------------------------------------

set Is_Playing, FALSE
set Is_Sleeping, FALSE
exit

;--------------------------------------------------
:GS_Init
;--------------------------------------------------

;traceon
AddModelKey Stand OnStand
AddModelKey Sleep, OnSleep

exit

