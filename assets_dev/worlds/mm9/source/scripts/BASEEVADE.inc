;------------------------------------------
;	BaseEvade.Inc
;	Jeff Leggett
;	09/07/2001
;
;	Basic Evasive Maneuvers..
;
;------------------------------------------

#include aiglobals.inc
#include basetimers.inc

#number				MIN_BACKPEDAL_OBSTACLE = 0.5
#number				g_bEvading = 0
#number				g_targetDirX
#number				g_targetDirY
#number				g_targetDirZ

#number				g_strafeDirX
#number				g_strafeDirY
#number				g_strafeDirZ

#number				g_bPickDir = 1
#number				g_nStrafeAngle = 45

#number				g_nLastObstacleTime = 0

#number				g_bBackpedalRun = 1
#number				g_bAttackStrafeRun = 1

;
; Defaults to a 3 second evade time...
;
#number				g_nEvadeTime = 3	
#number				g_nEvadeStart = 0

#number				g_nBackpedalPct = 0.5


;------------------------------------------
:BE_GetTargetDir
;------------------------------------------

	GetPos g_hMyObject, g_posX, g_posY, g_posZ
	GetPos g_hTarget, g_targetDirX, g_targetdirY, g_targetDirZ

	g_posY = g_targetdirY

	VecSub g_targetDirX, g_targetDirY, g_targetDirZ, g_posX, g_posY, g_posZ
	VecNorm g_targetDirX, g_targetDirY, g_targetDirZ

	Exit

;------------------------------------------
:BE_StrafeObstacle
;------------------------------------------

	gosub BE_BackpedalObstacle


	Exit TRUE

;------------------------------------------
:BE_AttackStrafeObstacle
;	
;	p0 - hObstacle
;
;------------------------------------------

	GetParam 0, g_hObject

	if ( g_hObject!=g_hTarget )
		Stop
		Exit TRUE
	Endif

	IsAttacking g_bTemp

	g_bTemp = TRUE

	if ( g_bTemp==TRUE )
		g_bBackpedalRun = FALSE
		gosub BE_Backpedal
		g_bBackpedalRun = TRUE
	else
		Stop
	Endif

	Exit TRUE

;------------------------------------------
:BE_AttackStrafe
;------------------------------------------
	gosub BE_GetTargetDir

	FaceDir g_targetDirX, g_targetDirY, g_targetDirZ, 360

	if ( g_bPickDir==TRUE )
		GetRandomInt 0,1, g_nRandom

		if (g_nRandom==0)
			g_nStrafeAngle = 45
		else
			g_nStrafeAngle = -45
		Endif
	Endif

	g_bPickDir = FALSE

	RotateDir g_targetDirX, g_targetDirY, g_targetDirZ, g_nStrafeAngle

	Strafe g_targetDirX, g_targetDirY, g_targetDirZ, g_bAttackStrafeRun
	OnObstacle BE_AttackStrafeObstacle

	Exit


;------------------------------------------
:BE_Strafe
;------------------------------------------
	gosub BE_GetTargetDir

	FaceDir g_targetDirX, g_targetDirY, g_targetDirZ, 360

	if ( g_bPickDir==TRUE )
		GetRandomInt 0,1, g_nRandom

		if (g_nRandom==0)
			g_nStrafeAngle = 65
		else
			g_nStrafeAngle = -65
		Endif
	Endif

	g_bPickDir = FALSE

	RotateDir g_targetDirX, g_targetDirY, g_targetDirZ, g_nStrafeAngle

	Strafe 	g_targetDirX, g_targetDirY, g_targetDirZ, TRUE
	OnObstacle BE_AttackStrafeObstacle

	Exit

;------------------------------------------
:BE_BackpedalTick
;------------------------------------------

	GetStat g_hMyObject, IsIdle, g_bTemp

	if ( g_bTemp==TRUE )
		; if we've stopped for some reason, then we don't want to continue with evading...
		Exit
	EndIf

	gosub BE_Strafe

	GetRandomFloat 0.1, 0.4, g_nRandom

	Wait BASE_EVADE_WAIT, g_nRandom, BE_BackpedalTick

	Exit

;------------------------------------------
:BE_BackpedalDone
;------------------------------------------

	gosub BE_BackpedalTick

	Exit

;------------------------------------------
:BE_BackpedalObstacle
; 
;	p0 - hObstacle
;	p1-3 - normal vector
;------------------------------------------

	GetParam 0, g_hObject

	if ( g_hObject!=g_hTarget )
		Stop
		Exit TRUE
	Endif

	GetTime g_nTemp

	g_nTemp = g_nTemp - g_nLastObstacleTime

	if ( g_nTemp < MIN_BACKPEDAL_OBSTACLE )
		; Keep us from "freaking out" too much... (ie: continuously banging against something...)
		Stop
		Exit TRUE
	EndIf

	GetTime g_nLastObstacleTime

	gosub BE_GetTargetDir
	
	Strafe 	g_targetDirX, 0, g_targetDirZ, TRUE

;;	gosub BE_BackPedal

	Exit TRUE

;------------------------------------------
:BE_Backpedal
;------------------------------------------

	gosub BE_GetTargetDir

	RotateDir g_targetDirX, g_targetDirY, g_targetDirZ, 180
	GetRandomInt 5, 35, g_nRandom
	GetRandomInt 0, 1, g_nTemp
	if ( g_nTemp==1 )
		g_nRandom = g_nRandom * -1
	EndIf

	RotateDir g_targetDirX, g_targetDirY, g_targetDirZ, g_nRandom

	Strafe 	g_targetDirX, 0, g_targetDirZ, g_bBackpedalRun

	RotateDir g_targetDirX, g_targetDirY, g_targetDirZ, 180
	FaceDir g_targetDirX, 0, g_targetDirZ, 360

	OnObstacle BE_BackpedalObstacle

	Exit


;------------------------------------------
:BE_BackpedalStart
;------------------------------------------

	g_bBackpedalRun = TRUE
	gosub BE_BackPedal	

	g_nTemp = g_nEvadeTime * g_nBackpedalPct

	GetTime g_nEvadeStart

	Wait BASE_EVADE_WAIT, g_nTemp, BE_BackpedalDone

	Exit


;------------------------------------------
:BaseEvadeStart
;------------------------------------------

	OnPathClear
	OnObstacle

	if ( g_hTarget==NULL )
		DebugOut What am I evading???
		Exit
	Endif
	
	g_bEvading = TRUE
	g_bPickDir = TRUE
	
	; See if we need to backpedal...

	gosub IsTargetMoving

	if ( g_bTemp==FALSE )
		gosub BE_BackpedalStart
		Exit
	EndIf

	gosub BE_GetTargetDir

	GetVelocity g_hTarget, g_velX, g_velY, g_velZ
	VecNorm g_velX, g_velY, g_velZ
	VecAngle g_dirX, g_dirY, g_dirZ, g_velX, g_velY, g_velZ, g_nTemp

	if ( g_nTemp < 0 )
		g_nTemp = g_nTemp * -1
	endif

	if ( g_nTemp < 30 )
		gosub BE_BackpedalTick
	else
		gosub BE_BackpedalStart
	endif

	Exit

;------------------------------------------
:BaseEvadeStop
;------------------------------------------
	
	OnTargetBeyondDist 0
	OnObstacle

	Wait BASE_EVADE_WAIT, 0, DoNothing
	g_bEvading = FALSE

	Exit
