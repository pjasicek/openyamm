;------------------------------------------
; Agressive1.inc
;
;	Aggresively go after target....
;
;
;	NOTE: this include is dependent on base.inc....
;
;------------------------------------------


#number		AGGRESIVE_TICK = 0.1

;------------------------------------------
:Aggresive1Tick
;------------------------------------------


	Exit

;------------------------------------------
:Aggresive1Start
;
;------------------------------------------
	Wait AGGRESIVE_WAIT, AGGRESIVE_TICK, Aggresive1Tick
	
	Exit
