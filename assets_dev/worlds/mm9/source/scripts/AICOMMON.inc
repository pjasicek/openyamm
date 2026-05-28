;---------------------------------------------------------------
;	AICommon.inc
;	Jeff Leggett
;	11/29/2001
;	
;	Data and functions that are common to all types of AI...
;
;---------------------------------------------------------------

#include AIGlobals.inc
#include BaseTimers.inc

#number				MAX_RESURRECT_DIST=1000

#number				g_bCanBeResurrected = 0

;
; Set true when we are resurrecting someone else AND when we are being resurrected...
;
#number				g_bResurrecting = 0
#number				g_bAskedForResurrection = 0

#number				MAX_OBJECTS=20
#numberArray		g_hObjectArray[20]
#hobject			g_hResurrect

#string				TMSG_RESURRECT="Resurrect"
#string				TMSG_RESURRECTME="ResurrectMe"

; Tracks who was my target when I died...
#hobject			g_hDeathTarget=0
#number				g_bCanResurrectNow=0

;--------------------------------------------------------
:AlertStart
;--------------------------------------------------------
	gosub AlertTick
	Exit

;--------------------------------------------------------
:AlertTick
;--------------------------------------------------------
	Wait ALERT_WAIT, g_nRandom, AlertTick

	if ( g_hTarget==NULL )
		Exit
	Endif

	SendAlert g_hTarget

	Exit

;--------------------------------------------------------
:AlertStop
;--------------------------------------------------------
	Wait ALERT_WAIT, 0, DoNothing
	Exit



;--------------------------------------------------------
:CanBeResurrected
;
;	returns TRUE or FALSE in g_bCanBeResurrected
;--------------------------------------------------------
	
	GetStat g_hMyObject,CanBeResurrected,g_bCanBeResurrected

	if ( g_bCanBeResurrected==FALSE )
		Exit
	Endif

	GetAnimNbr g_hMyObject,Resurrect,g_bCanBeResurrected
	if ( g_bCanBeResurrected==-1 )
		g_bCanBeResurrected	= FALSE
	else
		g_bCanBeResurrected = TRUE
	endif


	Exit

;---------------------------------------------------------------
:OnLinkBroken
;---------------------------------------------------------------

	GetParam 0, g_hObject
	if ( g_hObject==g_hAttacker )
		g_hAttacker = NULL
	Endif

	if ( g_hObject==g_hResurrect )
		g_hResurrect = NULL
	Endif

	if ( g_hObject==g_hDeathTarget )
		g_hDeathTarget = NULL
	endif

	Exit FALSE

;--------------------------------------------------------
:AskForResurrection
;
;
;	See if anyone nearby could potentially resurrect us.
;	if so, trigger them and see what happens...
;
;--------------------------------------------------------

	;;cprint LOOKING for someone to resurrect me...

	GetObjects AIBase,MAX_RESURRECT_DIST,MAX_OBJECTS,g_hObjectArray,g_nTemp

	if ( g_nTemp>0 )

		Sub g_nTemp,1

		while (g_nTemp>=0)
			
			ArrayGet g_hObjectArray, g_nTemp, g_hObject

			g_bTemp	= TRUE

			if ( g_hDeathTarget!=NULL )
				GetObjectTarget g_hObject,g_hObject2
				if ( g_hObject2!=NULL )
					if ( g_hObject2!=g_hDeathTarget )
						g_bTemp = FALSE
					Endif
				Endif
			Endif

			if ( g_bTemp==TRUE )
				IsObjectActive g_hObject,g_bTemp
			Endif

			if ( g_bTemp==TRUE )
				if ( g_hObject!=g_hMyObject )
					g_bTemp = FALSE
					GetStat g_hObject,IsResurrecter,g_bTemp

					if ( g_bTemp==TRUE )
						g_bAskedForResurrection = TRUE
						Trigger g_hObject,TMSG_RESURRECTME
						IsTurnBased g_bTemp
						if ( g_bTemp==TRUE )
							Wait RESURRECT_WAIT,4,AskForResurrection
						else
							Wait RESURRECT_WAIT,5,AskForResurrection
						Endif
						Exit
					Endif
				endif
			Endif

			Sub g_nTemp,1

		endwhile
	
	endif

	;cprint NO ONE TO RESURRECT ME! boo hoo...

	if ( g_bAskedForResurrection==TRUE )
		;;cprint removing myself...
	
		GetStat g_hMyObject,IsResurrecter,g_bTemp

		if ( g_bTemp==TRUE )
			; Just resurrect myself!
			GetRandomFloat 2,10,g_nRandom
			Wait RESURRECT_WAIT,g_nRandom,OnResurrect
			Exit
		Endif

;
;		If we've already asked to be resurrected, and it hasn't happened yet, and
;		there is no one around to resurrect us...  Time to go bye-bye...
;
		GetStat g_hMyObject,IsGibber,g_bTemp

		; Don't want gibbers do be removed.  There gibs will fall from the sky!

		if ( g_bTemp==FALSE )
			RemoveObject g_hMyObject
		Endif

	Endif

	Exit

;--------------------------------------------------------
:ResurrectMe
;
;	p0	- Who's asking for it...
;
;--------------------------------------------------------

	if ( g_hResurrect!=NULL )
	; currently we can only handle 1 at a time...
		;cprint I'VE BEEN REQUESTED TO RESURRECT SOMEONE, BUT I'M BUSY!
		Exit
	Endif

	;cprint I'VE BEEN REQUESTED TO RESURRECT SOMEONE...

	GetParam 0, g_hResurrect

	IsTurnBased g_bTemp
	
	if ( g_bTemp==TRUE )	
		GetRandomFloat 1,2,g_nRandom
	else
		GetRandomFloat 3,6,g_nRandom
	Endif

	Wait RESURRECT_WAIT,g_nRandom,DoResurrection

	Exit

;--------------------------------------------------------
:DoResurrection
;
;	Time to resurrect.  Be sure to override this function
;	to stop whatever it was that you were doing and then
;	call this function...
;
;--------------------------------------------------------

	if ( g_hResurrect==NULL )
		;cprint NO ONE TO RESURRECT??
		Exit
	Endif

	IsDead g_hMyObject,g_bTemp
	if ( g_bTemp==TRUE )
		g_hResurrect = NULL
		Exit
	Endif

	IsDead g_hResurrect,g_bTemp

	if ( g_bTemp==FALSE )
		g_hResurrect = NULL
		Exit
	Endif

	;cprint TIME TO RESURRECT HIM!!

	g_bResurrecting	= TRUE

	FaceObject g_hResurrect, 450

	PlayAnim ResurrectSpell, DoResurrectionDone

	Exit

;--------------------------------------------------------
:DoResurrectionTrigger
;--------------------------------------------------------

	;;cprint GOT resurrect trigger!

	if ( g_hResurrect==NULL )
		;;cprint NO ONE TO RESURRECT?
		Exit
	Endif

	if ( g_bResurrecting==FALSE )
		;;cprint I'M NOT RESURRECTING??
		Exit
	endif

	Trigger g_hResurrect,TMSG_RESURRECT

	BreakObjectLink g_hResurrect
	g_hResurrect	= NULL
	
	Exit

;--------------------------------------------------------
:DoResurrectionDone
;
;	Overload this...
;
;--------------------------------------------------------

	g_bResurrecting	= FALSE

	Exit

;-------------------------------------------------------
:CanResurrectNow
;-------------------------------------------------------
#numberArray			g_hArray[5]
#number					g_nArrayCount=0
#number					g_radius

	GetStat g_hMyObject,Radius,g_radius

	g_radius = g_radius * 2

	GetObjects Actor,g_radius,20,g_hArray,g_nArrayCount

	if ( g_nArrayCount!=0 )
		;;;cprint Somebody is too close... can't resurrect now...
		g_bCanResurrectNow = 0
		exit
	Endif

	;;;cprint OK, time to resurrect...
	g_bCanResurrectNow = 1

	exit


;--------------------------------------------------------
:OnResurrect
;
;	OK, time to resurrect... 
;
;	Set our Resurrect stat to TRUE and play our animation...
;
;--------------------------------------------------------

;
;	This will make us visible and put our bounding box
;	where it should be...
;

;
;	Cancel any pending resurrection requests...
;
	Wait RESURRECT_WAIT,0,DoNothing

	gosub CanResurrectNow

	if (g_bCanResurrectNow==FALSE)
		; Try again in 1/2 second...
		Wait RESURRECT_WAIT,0.5,OnResurrect
		Exit
	Endif


	SetStat g_hMyObject,Resurrect,TRUE
	PlayAnim Resurrect, ResurrectDone

	g_bResurrecting = true

	Exit

;--------------------------------------------------------
:ResurrectDone
;
;	Overload this to go back to being an evil bastard...
;	
;--------------------------------------------------------

	g_bResurrecting = FALSE

	Exit

;--------------------------------------------------------
:OnDeath
;
;	if we can be resurrected, notify any monsters that
;	can resurrect that we are ready!
;
;--------------------------------------------------------
	if ( g_bCanBeResurrected==FALSE )
		;;cprint I DIED and CANNOT be resurrected!
		Exit FALSE
	Endif

	SetStat g_hMyObject,WaitForResurrect,TRUE

	GetTarget g_hDeathTarget

	Target NULL

	if ( g_hDeathTarget!=NULL )
		CreateObjectLink g_hDeathTarget
	endif

	Exit FALSE

;---------------------------------------------------------------
:OnDeathDone
;---------------------------------------------------------------
	if ( g_bCanBeResurrected==TRUE )
		;;cprint I DIED and CAN be resurrected!
		gosub AskForResurrection
		g_bAskedForResurrection	= TRUE
		IsTurnBased g_bTemp
		if ( g_bTemp==TRUE )
			Wait RESURRECT_WAIT,2,AskForResurrection
		else
			Wait RESURRECT_WAIT,5,AskForResurrection
		Endif

		g_bCanBeResurrected	= FALSE
	endif
	exit FALSE

;---------------------------------------------------------------
:SetupAttacker
;---------------------------------------------------------------
	if ( g_hAttacker==NULL )
		; wtf?
		Exit
	endif

	IsFriend g_hAttacker, g_bTemp

	if ( g_bTemp==TRUE )
		g_hAttacker = NULL
		Exit
	Endif

	CreateObjectLink g_hAttacker

	Exit

;---------------------------------------------------------------
:ClearAttacker
;---------------------------------------------------------------
	if ( g_hAttacker!=NULL )
		BreakObjectLink g_hAttacker
		g_hAttacker	= NULL
	endif
	Exit

;---------------------------------------------------------------
:OnHateAll
;---------------------------------------------------------------

	AddEnemy AIBase
	Exit

;---------------------------------------------------------------
:OnStopHateAll
;---------------------------------------------------------------

	RemoveEnemy AIBase
	Exit


;---------------------------------------------------------------
:OnHateAllOthers
;---------------------------------------------------------------
	AddEnemy AIBase

	GetClassName g_hMyObject, g_sTemp
	AddFriend g_sTemp

	Exit

;---------------------------------------------------------------
:OnStopHateAllOthers
;---------------------------------------------------------------

	RemoveEnemy AIBase
	GetClassName g_hMyObject, g_sTemp
	RemoveFriend g_sTemp
	
	Exit


;--------------------------------------------------------
:ClearTarget
;
;	This is overloaded everywhere....
;
;--------------------------------------------------------

	Stop
	g_hTarget = NULL
	Target NULL

	Exit

;--------------------------------------------------------
:OnEnrage
;
;	Just stop and clear our target.
;	OnFoundTarget will take over from there....
;
;--------------------------------------------------------

	gosub ClearTarget

	Exit

;--------------------------------------------------------
:OnEnrageDone
;
;	Just stop and clear our target.
;	OnFoundTarget will take over from there....
;
;--------------------------------------------------------

	gosub ClearTarget

	Exit


;---------------------------------------------------------------
:InitCommon
;---------------------------------------------------------------
	GetMyHandle g_hMyObject

	OnDeath						OnDeath
	OnDeathDone					OnDeathDone
	OnObjectLinkBroken			OnLinkBroken
	OnEnrage					OnEnrage
	OnEnrageDone				OnEnrageDone

	gosub CanBeResurrected

;
;	If we're able to Resurrect others, setup a callback
;	for the resurrectme request...
;
	GetStat g_hMyObject,IsResurrecter,g_bTemp

	if ( g_bTemp==TRUE )
		AddTrigger TMSG_RESURRECTME,ResurrectMe
		AddModelKey DoResurrection, DoResurrectionTrigger
	Endif

	if ( g_bCanBeResurrected==TRUE )
		AddTrigger TMSG_RESURRECT,OnResurrect
	endif

	AddTrigger HateAll, OnHateAll
	AddTrigger StopHateAll, OnStopHateAll

	AddTrigger HateAllOthers, OnHateAllOthers
	AddTrigger StopHateAllOthers, OnStopHateAllOthers

	Exit

