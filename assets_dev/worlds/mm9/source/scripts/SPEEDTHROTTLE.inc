;------------------------------------------
;	SpeedThrottle.inc
;	Jeff Leggett
;
;	Used for throttling the AI's speed 
;	during attacks so that we can stick
;	with him if he's moving...
;
;------------------------------------------

#include aiglobals.inc
#include baseTimers.inc
#include baseEvade.inc



#number				g_throttleSpeed = 0

#number				g_bStrafeAttack = 0


;------------------------------------------
:SpeedThrottleStop
;------------------------------------------
	Wait SPEED_THROTTLE_WAIT, 0, DoNothing
	SetStat g_hMyObject, RunVel, g_runVel
	SetStat g_hMyObject, WalkVel, g_walkVel

	Exit

;------------------------------------------
:SpeedThrottleStart
;------------------------------------------
	Wait SPEED_THROTTLE_WAIT, 0.1, SpeedThrottleTick
	Exit

;------------------------------------------
:SpeedThrottleTick
;
;	If we are within attack range, throttle
;	our speed to match the targets...
;
;------------------------------------------
	Wait SPEED_THROTTLE_WAIT, 0.1, SpeedThrottleTick

	if (g_hTarget==NULL)
		Exit
	Endif

	IsMoving g_bTemp

	if ( g_bTemp==FALSE )
		Exit
	Endif

	g_throttleSpeed = g_runVel

	GetStat g_hMyObject, Lunging, g_bTemp
	if ( g_bTemp==TRUE )
		; We are lunging...
		Mul g_throttleSpeed, 1.25
	EndIf

	AIGetDistance g_hTarget, g_nDist

	g_nTemp = g_attackRange * 0.9

	if ( g_nDist >= g_nTemp )
		SetStat g_hMyObject, RunVel, g_throttleSpeed
		Exit
	EndIf

;
; OK, let's do some throttling....
;
	GetVelocity g_hTarget, g_velX, g_velY, g_velZ
	VecMag g_velX, g_velY, g_velZ, g_nTemp

	if ( g_nTemp < 20 )
		; They aren't moving very fast, should we slow down?

		IsAttacking g_bTemp

		if ( g_bTemp==TRUE )
			if ( g_bAttackPerformed==FALSE )
				if ( g_bStrafeAttack==TRUE )
					if ( g_bTemp==TRUE )
						; We're strafe attacking and haven't hit them yet....
						; Let's slow down a wee bit....
						g_throttleSpeed = g_runVel * 0.5
						SetStat g_hMyObject, RunVel, g_throttleSpeed
						Exit
					Endif
				Endif
			Endif
		Endif

		SetStat g_hMyObject, RunVel, g_runVel
		SetStat g_hMyObject, WalkVel, g_walkVel
		Exit
	EndIf


	g_throttleSpeed = g_nTemp

;
; Get the angle they are moving...
;
	VecNorm g_velX, g_velY, g_velZ

	gosub BE_GetTargetDir

	VecAngle g_targetDirX, 0, g_targetDirZ, g_velX, 0, g_velZ, g_nTemp

	if ( g_nTemp < 0 )
		Mul g_nTemp, -1
	Endif

	if ( g_nTemp > 45 )
		SetStat g_hMyObject, RunVel, g_runVel
		SetStat g_hMyObject, WalkVel, g_walkVel
		Exit
	Endif

	Mul g_throttleSpeed, 0.95

	if ( g_throttleSpeed < g_runVel )
		SetStat g_hMyObject, RunVel, g_throttleSpeed
		SetStat g_hMyObject, WalkVel, g_throttleSpeed
	else
		SetStat g_hMyObject, RunVel, g_runVel
		SetStat g_hMyObject, WalkVel, g_walkVel
	Endif

	Exit


;------------------------------------------
:SpeedThrottleInit
;------------------------------------------
	GetMyHandle g_hMyObject

	GetStat g_hMyObject, RunVel, g_runVel
	GetStat g_hMyObject, WalkVel, g_walkVel
	GetStat g_hMyObject, AttackRange, g_attackRange
	

	Exit