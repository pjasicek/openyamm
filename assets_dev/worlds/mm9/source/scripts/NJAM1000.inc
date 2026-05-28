;----------------------------------------------
;Njam1000.inc
; By Timmy
; 11/16
; Makes Njam disappear after he's hit a lot

;----------------------------------------------

#include globals.inc 



#number							nHPRange


; flag variables
#number							Visible = 1
#number							Solid   = 8192
#number							Gravity = 131072


;-------------------------------------
:ShouldRunAway
;-------------------------------------

getmyhandle g_hmyobject
getstat g_hmyobject HitPoints g_ntemp
if (g_ntemp<nHPRange)
	Gosub Vanish
	exit
endif

gosub ShouldRunAway, 1
exit



;-------------------------------------
:Vanish
;-------------------------------------
getmyhandle g_hmyobject

; play vanish effect here
DoClientFX g_hmyObject,GreaterDemon
Playsound \Sounds\magic\Windup10.wav, DoNothing, 100, 24000, FALSE, 100
wait 1 1 Vanish2b
exit

;-------------------------------------
:Vanish2b
;-------------------------------------

clearflag g_hmyobject visible
Playsound \Sounds\magic\teleport.wav, DoNothing, 100, 24000, FALSE, 100
wait 1 1 Vanish2c
exit


;-------------------------------------
:Vanish2c
;-------------------------------------
removeobject g_hmyobject
exit


;-------------------------------------
:Init
;-------------------------------------

SetPropNumber CanDamage, FALSE

getrandomint 1500, 4500 nHPRange
exit
