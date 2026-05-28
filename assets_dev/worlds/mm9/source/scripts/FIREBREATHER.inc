;------------------------------
;	FireBreather.inc
;	by SJR
;	Purpose:fire eater at a
;			carnival.
;------------------------------
#include BaseGlobals.inc

#string		fire_sShooterName = ""
#hobject	fire_hShooter = 0
#hobject	fire_hMe = 0

#number		fire_xDir = 0
#number		fire_yDir = 0
#number		fire_zDir = 0

#number		fire_xMe = 0
#number		fire_yMe = 0
#number		fire_zMe = 0

;------------------------------
:InitFireBreather
;------------------------------
	GetMyHandle fire_hMe

	Exit TRUE

;------------------------------
:BreatheFire
;------------------------------
	if( fire_hShooter==0 )
		GetObjectHandle fire_sShooterName, fire_hShooter
		if( fire_hShooter==0 )
cprint FireBreather.inc retrieved NULL shooter!
			Exit TRUE
		endif
	endif
;cprint fire_sShooterName
;cprint fire_hShooter
	gosub OrientShooter
	gosub StartFire
	Wait 0, 3, EndFire

	Exit TRUE

;------------------------------
:OrientShooter
;------------------------------
	GetFaceDir fire_hMe, fire_xDir,fire_yDir,fire_zDir
	GetPOS fire_hMe, fire_xMe,fire_yMe,fire_zMe

	SetPOS fire_hShooter, fire_xMe,fire_yMe,fire_zMe
	SetRotation fire_hShooter, fire_xDir,fire_yDir,fire_zDir

	Exit TRUE

;------------------------------
:StartFire
;------------------------------
	Trigger fire_hShooter, on

	Exit TRUE

;------------------------------
:EndFire
;------------------------------
	Trigger fire_hShooter, off

	Exit TRUE