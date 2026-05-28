;-----------------------------------------------------
; BaseTimers.inc
; Jeff Leggett
;
;	Wait timers are all defined here so that we don't
;	override them...
;
;	Timers 1-20 are used by include (.inc) scripts.
;	.SCR scripts should use 20-30.  0 can be used by
;	either as a one-time update.
;-----------------------------------------------------


#number				ATTACK_CHECK_WAIT		= 1
#number				CHASE_TARGET_WAIT		= 2
#number				MELEE_CHECK_WAIT		= 3
#number				WANDER_WAIT				= 4
#number				WANDER_LEASH_WAIT		= 5
#number				BASE_WAIT_NBR			= 6
#number				AGGRESSIVE_WAIT 		= 7
#number				RUN_AWAY_WAIT			= 8
#number				HIDE_WAIT				= 9
#number				SPEED_THROTTLE_WAIT		= 10
#number				BASE_EVADE_WAIT			= 11
#number				ALERT_WAIT				= 12
#number				RESURRECT_WAIT			= 13
#number				TAUNT_WAIT				= 14

