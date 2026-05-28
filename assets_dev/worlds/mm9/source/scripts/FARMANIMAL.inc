;---------------------------------------------------
;	FarmAnimal.Inc
;	Jeff Leggett
;
;	Just wander around.
;	If damaged, run away...
;
;---------------------------------------------------

#include BaseWander.Inc
#include BaseRun.Inc


;---------------------------------------------------
:FarmInitWander
;---------------------------------------------------
	gosub BaseWanderInit

	Exit

;---------------------------------------------------
:EnableWandering
;---------------------------------------------------
	gosub BaseWanderStart
	Exit

;---------------------------------------------------
:DisableWandering
;---------------------------------------------------
	gosub BaseWanderStop
	Exit

;---------------------------------------------------
:OnDamage
;---------------------------------------------------

	if ( g_hTarget!=NULL )
		exit FALSE
	endif

	GetParam 0,g_hTarget
	Target g_hTarget, FALSE

	Exit FALSE

;---------------------------------------------------
:BaseRunCancel
;---------------------------------------------------
	gosub BaseRunCancel,1

	Target NULL
	g_hTarget = NULL

	stop
	gosub EnableWandering

	Exit

;---------------------------------------------------
:BaseRunAway
;---------------------------------------------------

	gosub DisableWandering
	gosub BaseRunAway,1

	Exit

;---------------------------------------------------
:OnDamageDone
;---------------------------------------------------

	if ( g_hTarget!=NULL )
		gosub BaseRunAway
	Endif
	
	Exit
	

;---------------------------------------------------
:OnTargetDead
;---------------------------------------------------
	Target NULL
	g_hTarget = NULL
	gosub BaseRunCancel

	Exit

;---------------------------------------------------
:BaseShouldRun
;	Farm animals always run..
;---------------------------------------------------

	g_bTemp = TRUE
	Exit

;---------------------------------------------------
:FarmAnimalInit
;---------------------------------------------------

	SetPropNumber WanderWaitMin, 10
	SetPropNumber WanderWaitMax, 20

	gosub BaseRunInit

	Wait 0, 0.1, FarmInitWander

	OnDamage OnDamage
	OnDamageDone OnDamageDone
	OnTargetDead OnTargetDead

	Exit

