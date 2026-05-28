;--------------------------------------------------------------
;	BotMove.inc
;
;		Bot movement code... (During combat...)
;
;--------------------------------------------------------------

#include botGlobals.inc

;--------------------------------------------------------------
; Strafe Directions
;--------------------------------------------------------------
#number			SD_NONE			= 0
#number			SD_LEFT			= 1
#number			SD_RIGHT		= 2
#number			SD_FORWARD		= 3
#number			SD_BACK			= 4

#number			bm_strafeLR		= 0
#number			bm_strafeFB		= 0


#number			bm_strafeDirX
#number			bm_strafeDirY
#number			bm_strafeDirZ


;------------------------------------------
:BM_ProjectileAvoidDone
;
;------------------------------------------

	Stop
;;; todo--> Do user callback here...
;;;	OnProjectile BB_OnProjectile, 200

	Exit

;------------------------------------------
:BM_AvoidProjectile
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
	Wait EVADE_WAIT, 0.3, BM_ProjectileAvoidDone

	Exit


;------------------------------------------
:BM_DoStrafe
;
;	Looks at the strafe code and then
;	does the strafe in the correct direction
;------------------------------------------
	
	if ( bm_strafeLR==SD_NONE )
		Set dirX, 0
		Set dirY, 0
		Set dirZ, 0
	else
		if ( bm_strafeLR==SD_LEFT )
			GetLeftDir dirX, dirY, dirZ
		else
			GetRightDir dirX, dirY, dirZ
		endif
	endif

	if ( bm_strafeFB==SD_NONE )
		Set bm_strafeDirX, 0
		Set bm_strafeDirY, 0
		Set bm_strafeDirZ, 0
	else
		if ( bm_strafeFB==SD_FORWARD )
			GetForwardDir bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ
		else
			GetReverseDir bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ
		endif
	endif

	VecAdd bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ, dirX, dirY, dirZ
	VecNorm bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ
	Strafe bm_strafeDirX, bm_strafeDirY, bm_strafeDirZ, TRUE

	Exit

;------------------------------------------
:BM_MoveTick
;
;	See if we need to move closer or
;	farther away from the target...
;
;------------------------------------------

;
; Decide if we want to move forward or back...
;
	Set bm_strafeFB, SD_NONE

	if ( g_hTarget!=NULL )
		AIGetDistance g_hTarget, g_nTemp
		if ( g_nTemp > 320 )
			Set bm_strafeFB, SD_FORWARD
		endif

		if ( g_nTemp < 140 )
			Set bm_strafeFB, SD_BACK
		endif
	endif

	Wait EVADE_MOVE_WAIT, 0.4, BM_MoveTick

	Exit

;------------------------------------------
:BM_EvadeTick
;------------------------------------------

	if ( bm_strafeLR==SD_LEFT )
		Set bm_strafeLR, SD_RIGHT
	else
		if ( bm_strafeLR==SD_RIGHT )
			Set bm_strafeLR, SD_LEFT
		endif
	endif

	gosub BM_DoStrafe

	Wait EVADE_WAIT, 0.8, BM_EvadeTick
	
	Exit

;------------------------------------------
:BM_SetupEvade
;
;	For now, just keep strafing back and 
;	forth...
;------------------------------------------

	;; SetCrouch TRUE

	GetRandomInt SD_LEFT,SD_RIGHT, bm_strafeLR

	gosub BM_EvadeTick
	gosub BM_MoveTick

	Exit

;------------------------------------------
:BM_CancelEvade
;
;	Just stop our wait tick...
;------------------------------------------
	
	Wait EVADE_WAIT, 0, DoNothing

	Exit

