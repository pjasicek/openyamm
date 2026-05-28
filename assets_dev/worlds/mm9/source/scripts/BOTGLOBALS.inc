;--------------------------------------------------------------
;	BotGlobals.Inc
;
;	Globals that are shared by the various Bot include files..
;
;--------------------------------------------------------------

#include aiglobals.inc

#hobject			hProjectile
#number				bHeadingToward
#number				velX
#number				velY
#number				velZ
#number				angle

#number				dirX
#number				dirY
#number				dirZ

;
; Our wait callback ids...
;
#number				ATTACK_WAIT			= 1
#number				EVADE_WAIT			= 2
#number				EVADE_MOVE_WAIT		= 3
#number				MISSION_WAIT		= 4


#number				attackTime = 0.4
#number				attackCount = 0

#hobject			hLastAttacker = 0


;------------------------------------------
:DoNothing
;
;	Used to kill callbacks...
;
;------------------------------------------
	Exit
