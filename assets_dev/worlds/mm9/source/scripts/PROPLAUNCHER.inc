;----------------------------------------------------------
;	PropLauncher.Inc
;	Jeff Leggett
;	12/06/2001
;	
;
;	Script that can turn a prop (or any model) into a projectile...
;
;
;	Be sure to call PropLauncherInit in your main...
;----------------------------------------------------------

#include globals.inc
#include flags.inc

#number			targetX
#number			targetY
#number			targetZ

#number			homeX
#number			homeY
#number			homeZ

#number			bThrowing = 0

#number			rotX = 0
#number			rotY = 0
#number			rotZ = 1

#hobject		hRequester = 0
#number			bDidDamage = 0

#number			g_nThrowSpeed = 500
#number			g_nRotationRate = 450

#number			g_nPredictOffsetMin = 0.6
#number			g_nPredictOffsetMax = 0.9

#number			g_nDamageMin = 1
#number			g_nDamageMax = 3

#number			velocity


#hobject		g_hTarget = 0

#number			g_lastLaunchTime=0


;----------------------------------------------------------
:KeepRotating
;----------------------------------------------------------
	if (bThrowing==TRUE)
		Rotate rotX,rotY,rotZ,90,g_nRotationRate,KeepRotating
	Endif

	Exit

;----------------------------------------------------------
:DoRotation
;----------------------------------------------------------

	gosub KeepRotating

	Exit

;----------------------------------------------------------
:ThrowAtTarget
;----------------------------------------------------------
	GetPos g_hTarget, targetX,targetY,targetZ
	GetPos g_hMyObject, g_posX, g_posY, g_posZ

	VecDist g_posX,g_posY,g_posZ,targetX,targetY,targetZ,g_nTemp

	if ( g_nTemp > 60 )

		GetVelocity g_hTarget,g_velX,g_velY,g_velZ
		g_velY = 0

		VecMag g_velX,g_velY,g_velZ,velocity

		if ( velocity > 20 )

;			adjust position based on velocity...
;			how much time to intercept

			g_nTemp = g_nTemp / g_nThrowSpeed

			GetRandomFloat g_nPredictOffsetMin,g_nPredictOffsetMax,g_nRandom

			g_nTemp = g_nTemp * g_nRandom

;;			VecNorm g_velX,g_velY,g_velZ
			VecScale g_velX,g_velY,g_velZ,g_nTemp
			VecAdd targetX,targetY,targetZ,g_velX,g_velY,g_velZ
		endif
	endif

	VecSub targetX,targetY,targetZ,g_posX,g_posY,g_posZ
	VecNorm targetX,targetY,targetZ
	FaceDir targetX,targetY,targetZ
	VecScale targetX,targetY,targetZ,g_nThrowSpeed

	SetVelocity g_hMyObject,targetX,targetY,targetZ
	SetFlag g_hMyObject,FLAG_VISIBLE

	bThrowing = TRUE
	bDidDamage = FALSE

	gosub DoRotation

	GetTime g_lastLaunchTime

	Wait 5,5,Reset

	Exit

;----------------------------------------------------------
:ThrowAtPlayerTrigger
;
;	p0 - requester...
;----------------------------------------------------------
	GetParam 0, g_hObject

	if ( g_hObject!=hRequester )
		if ( hRequester!=NULL )
			BreakObjectLink hRequester
		endif
		hRequester = g_hObject
		CreateObjectLink hRequester
	endif

	GetPlayerHandle g_hTarget

	gosub ThrowAtTarget

	exit

;----------------------------------------------------------
:Reset
;----------------------------------------------------------

	if ( hRequester!=NULL )
		Trigger hRequester,PropLauncherDone
	Endif

	Wait 5,0,DoNothing
	ClearFlag g_hMyObject,FLAG_VISIBLE
	SetVelocity g_hMyObject,0,0,0
	bThrowing = FALSE
	wait 7,0.1,ResetPosition

	bDidDamage = FALSE

	exit

;----------------------------------------------------------
:OnTouchNotify
;----------------------------------------------------------
	GetParam 0, g_hObject

	if ( g_hObject==hRequester )
		Exit FALSE
	Endif

	if ( bDidDamage==FALSE )
		IsClass g_hObject,Actor,g_bTemp
		if ( g_bTemp==TRUE )
			bDidDamage = TRUE
			GetRandomInt g_nDamageMin,g_nDamageMax,g_nTemp
			Damage g_hObject,g_nTemp,0
		else
			GetTime g_nTemp
			Sub g_nTemp,g_lastLaunchTime
			if ( g_nTemp < 0.2 )
				; Too soon to call it quits?
				Exit FALSE
			endif
		Endif
	Endif

;
;	TODO:Play sound here...
;
	gosub Reset

	exit


;----------------------------------------------------------
:ResetPosition
;----------------------------------------------------------

	SetPos g_hMyObject,homeX,homeY,homeZ

	exit

;----------------------------------------------------------
:OnLinkBroken
;----------------------------------------------------------
	
	GetParam 0,g_hObject
	if ( g_hObject==hRequester )
		hRequester = NULL
	endif
	
	exit

;----------------------------------------------------------
:PropLauncherInit
;----------------------------------------------------------

	GetMyHandle g_hMyObject
	ClearFlag g_hMyObject,FLAG_VISIBLE
	ClearFlag g_hMyObject,FLAG_SOLID

	GetPos g_hMyObject,homeX,homeY,homeZ
	
	AddTrigger ThrowAtPlayer,ThrowAtPlayerTrigger
	AddTrigger GetPlayer,ThrowAtPlayerTrigger
	AddTrigger ResetPosition,ResetPosition
	OnTouchNotify OnTouchNotify
	OnObjectLinkBroken OnLinkBroken

	SetStat g_hMyObject,GroundTouchNotify,TRUE

	Exit

