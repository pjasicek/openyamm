;----------------------------------------------------------------
;	WanderAir.inc
;	Jeff Leggett
;	2/22/2000
;
;	Include file used by creatures that fly around.... (wander)
;
;----------------------------------------------------------------

#include aiglobals.inc

#number						MAX_DIST_FROM_STARTPOINT=750

#number						g_turnRate
#number						g_turnDeg

#number						g_startX
#number						g_startY
#number						g_startZ

#number						g_dist

#number						g_defaultLaunchAlt=200

;----------------------------------------------------------------
:WanderAirObstacle
;	p0		- handle to obstacle
;	p1-3	- Normal of the collision... 
;
;	For now, just go the opposite direction +- a little..
;----------------------------------------------------------------

	GetParam 1, g_rotX
	GetParam 2, g_rotY
	GetParam 3, g_rotZ

	GetRandomFloat -0.20, 0.20, g_nRandom
	Add g_rotX, g_nRandom

	GetRandomFloat -0.20, 0.20, g_nRandom
	Add g_rotZ, g_nRandom

	FaceDir g_rotX, g_rotY, g_rotZ, 90
	Walk

	GetRandomFloat 3, 10, g_nRandom
	Wait 0, g_nRandom, WanderAirGo

	exit TRUE

;----------------------------------------------------------------
:WanderAirGo
;
;	Picks a direction and goes...
;----------------------------------------------------------------

	GetRandomFloat 15, 90, g_turnDeg
;;	GetRandomFloat 20, 50, g_turnRate

	Set g_turnRate, g_turnDeg

	GetPos g_hMyObject, g_posX, g_posY, g_posZ

	CalcDist g_posX,g_posY,g_posZ,g_startX,g_startY,g_startZ,g_dist

	if (g_dist>MAX_DIST_FROM_STARTPOINT)
		; Too far away from original starting point!!
		FacePos g_startX, g_startY, g_startZ, 180
	else
		GetRandomInt 0,1, g_nRandom

		if ( g_nRandom==0 )
			Mul g_turnDeg, -1
		endif

		Rotate 0,1,0,g_turnDeg,g_turnRate
	endif

	Walk

	GetRandomFloat 3, 10, g_nRandom
	Wait 0, g_nRandom, WanderAirGo

	Exit

;----------------------------------------------------------------
:WanderAirStuck
;----------------------------------------------------------------

	gosub WanderAirGo
	exit TRUE

;----------------------------------------------------------------
:WanderAirStartup
;----------------------------------------------------------------

	GetPos g_hMyObject, g_startX, g_startY, g_startZ

	IsOnGround g_bTemp

	if ( g_bTemp==TRUE )
		Launch WanderAirGo, g_defaultLaunchAlt
	else
		gosub WanderAirGo
	endif

	exit TRUE

;----------------------------------------------------------------
:WanderAirInit
;----------------------------------------------------------------

	GetMyHandle	g_hMyObject
	OnObstacle WanderAirObstacle
	OnStuck WanderAirStuck

	; Must Wait 0, and do some stuff after initial execution...
	Wait 0, 0.1, WanderAirStartup

	exit
