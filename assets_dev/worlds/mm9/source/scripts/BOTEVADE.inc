;--------------------------------------------------------------
;	BotEvade.inc
;
;		Evasive maneuver functions...
;
;	Note:
;		Include BotGlobals.Inc prior to this inc file.
;--------------------------------------------------------------

#include botbase.inc

;------------------------------------------
:BE_ProjectileAvoidDone
;
;
;------------------------------------------

	Stop
	OnProjectile BB_OnProjectile, 200

	Exit

;------------------------------------------
:BE_AvoidProjectile
;
;	See which way it's coming and strafe
;	away from it....
;
;------------------------------------------

	GetVelocity hProjectile, velX, velY, velZ
	VecNorm velX, velY, velZ

	Set g_nTemp, 90
	GetRandomInt 0,1, g_nRandom

	if ( g_nRandom==1 )
		Mul g_nTemp, -1
	endif
		
	RotateDir velX, velY,velZ, g_nTemp

	FaceDir velX, velY, velZ
	OnProjectile
	Run 
	Wait EVADE_WAIT, 0.3, BE_ProjectileAvoidDone

	Exit


;------------------------------------------
:BE_StrafeRight
;------------------------------------------
	GetRightDir dirX, dirY, dirZ
	Strafe dirX, dirY, dirZ, TRUE
	Wait EVADE_WAIT, 0.8, BE_EvadeRightTick

	Exit

;------------------------------------------
:BE_StrafeLeft
;------------------------------------------
	GetLeftDir dirX, dirY, dirZ
	Strafe dirX, dirY, dirZ, TRUE
	Wait EVADE_WAIT, 0.8, BE_EvadeLeftTick

	Exit

;------------------------------------------
:BE_EvadeRightTick
;------------------------------------------
	gosub BE_StrafeLeft
	Exit

;------------------------------------------
:BE_EvadeLeftTick
;
;------------------------------------------
	gosub BE_StrafeRight

	Exit

;------------------------------------------
:BE_SetupEvade
;
;	For now, just keep strafing back and 
;	forth...
;------------------------------------------

	;; SetCrouch TRUE
	gosub BE_StrafeLeft

	Exit

;------------------------------------------
:BE_CancelEvade
;
;	Just stop our wait tick...
;------------------------------------------
	
	Wait EVADE_WAIT, 0, DoNothing

	Exit

