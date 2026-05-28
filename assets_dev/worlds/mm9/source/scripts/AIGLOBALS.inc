;-------------------------------------------------------------------
;	AIGLOBALS.INC
;
;	Put commonly used AI global variables here....
;-------------------------------------------------------------------

#include globals.inc

#number				WALKRUNMODE_FORWARD = 0
#number				WALKRUNMODE_REVERSE = 1
#number				WALKRUNMODE_TARGET = 2


#hobject			g_hTarget=0					; Handle to the current target
#number				g_bInAttackRange=0			; Updated using OnAttackReady and OnTargetOutOfRange
#hobject			g_hAttacker=0				; Handle to attacker that damaged us.
#number				g_bAttacking=0				; set to true when we are attacking...
#number				g_bCanAttack=0				; Set to true when our attack wait is over....
#number				g_bFighting=0				; set to true when we've taken damage, or we've attacked player..

#number				g_nLastAttackTime=0			; Last time AI attacked its target...

#number				g_attackRange = 0


#number				g_normalX
#number				g_normalY
#number				g_normalZ

#number				g_targetX = 0
#number				g_targetY = 0
#number				g_targetZ = 0

#number				g_dirX
#number				g_dirY
#number				g_dirZ

#number				g_runVel = 0
#number				g_walkVel = 0
#number				g_bLunging = 0

#number				g_bAttackPerformed = 0

#number				g_nDist1
#number				g_nDist2


;------------------------------------------
:IsTargetMoving
;
;	Returns TRUE or FALSE in g_bTemp
;
;------------------------------------------
	g_bTemp = FALSE

	if (g_hTarget==NULL)
		Exit
	Endif

	GetVelocity g_hTarget, g_velX, g_velY, g_velZ

	VecMag g_velX, 0, g_velZ, g_nTemp

	if ( g_nTemp > 20 )
		g_bTemp = TRUE
	Endif

	Exit
