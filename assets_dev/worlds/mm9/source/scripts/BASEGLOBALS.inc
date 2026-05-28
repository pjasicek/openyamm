;------------------------
;	BaseGlobals.inc
;	by SJR
;	Purpose:cut down on
;			unneeded vars
;			and provide much needed
;			stop callback!
;------------------------

#number		TRUE	= 1
#number		FALSE	= 0

#hobject	NULL	= 0

;------------------------
:DoNothing
;------------------------
	Exit TRUE

;------------------------
:StopMoving
;------------------------
	Stop
	Exit TRUE