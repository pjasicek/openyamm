;----------------------------------------------------------------
;	NPCBASE.INC
;	Jeff Leggett
;	08/09/2001
;
;	Behavior:
;
;		- Wander around using basewander script.  If the USE
;		key is used on us, then this script will be paused.
;		And the RUDE system will take over....
;		
;		- If projectiles have been used near us, or we've been
;		damaged, then we'll run away from the attacker.
;
;		- Occasionally, we'll look for another NPC to walk over
;		and talk to.
;
;----------------------------------------------------------------

#include basewander.inc
#include baserun.inc

#number				SOCIALIZE_WAIT = 11

; How fast / often to look for someone to chat with?
;#number				MAX_SOCIALIZE_WAIT = 60
;#number				MIN_SOCIALIZE_WAIT = 15
#number				MAX_SOCIALIZE_WAIT = 15
#number				MIN_SOCIALIZE_WAIT = 5

; Once you are looking, how long to look for?
#number				MIN_CHAT_SEARCH = 5
#number				MAX_CHAT_SEARCH = 10

; Now that you're chatting, how long to chat for?
#number				CHAT_MIN = 10
#number				CHAT_MAX = 30

#number				g_bSocializeEnabled = 1
#number				g_bChatEnabled = 1
#number				g_bChatting = 0


#string				dest
#hObject			current_marker=0
#number             current_marker_xpos
#number             current_marker_ypos
#number             current_marker_zpos


;------------------------------------------
:EnableWandering
;
;	Do all things necessary to enable
;	Wandering...
;
;------------------------------------------

	gosub BaseWanderStart

	Exit

;----------------------------------------------------------------
:DisableWandering
;----------------------------------------------------------------
	gosub BaseWanderStop
	OnObstacle
	OnStuckDone
	OnStuck

	Exit


;----------------------------------------------------------------
:CancelChat
;----------------------------------------------------------------

	GetTarget g_hTarget
	
	if ( g_hTarget!=NULL )
		Trigger g_hTarget,GoodBye
	endif

	g_bChatting = FALSE

	Target NULL
	g_hTarget = NULL


	Wait SOCIALIZE_WAIT, 0, DoNothing

	Exit

;----------------------------------------------------------------
:EnableChat
;----------------------------------------------------------------

	g_bChatEnabled = TRUE

	if ( g_bSocializeEnabled==TRUE )
		gosub SetupNextChat
	endif

	Exit


;----------------------------------------------------------------
:DisableChat
;----------------------------------------------------------------

	gosub CancelChat
	gosub LookForPersonOff
	g_bChatEnabled = FALSE

	Exit


;----------------------------------------------------------------
:OnGoToLocArrival
;
;----------------------------------------------------------------
	
	current_marker = NULL
	Stop
	SetIdle

	gosub EnableChat
	gosub EnableWandering
	trigger g_hObject, HasArrived

	Exit

;----------------------------------------------------------------
:OnWarpToLoc
;
;----------------------------------------------------------------


	gosub DisableWandering
	gosub DisableChat
	Stop
	SetIdle
	
	GetStatStr g_hMyObject, PARAM, dest
	GetObjectHandle dest, current_marker
	GetPos current_marker, current_marker_xpos, current_marker_ypos, current_marker_zpos
	SetPos g_hMyObject, current_marker_xpos, current_marker_ypos, current_marker_zpos
	gosub OnGoToLocArrival

	Exit

;----------------------------------------------------------------
:OnGoToLoc
;
;----------------------------------------------------------------
	gosub DisableWandering
	gosub DisableChat

	Stop
	SetIdle

	GetStatStr g_hMyObject, PARAM, dest
	GetObjectHandle dest, current_marker
	WalkTo current_marker, 0, OnGoToLocArrival
	
	Exit

;----------------------------------------------------------------
:BuggerOff
;
;
;	Assumes g_hObject is filled with someone attempting to 
;	chat with us...
;----------------------------------------------------------------

	debugout BuggerOff!!!

	Trigger g_hObject,LeaveMeAlone

	Exit

;----------------------------------------------------------------
:OnHello
;
;	p0 - handle of trigger sender...
;----------------------------------------------------------------

	;;DebugOut OnHello

	GetParam 0, g_hObject
	GetTarget g_hTarget

	if ( g_bChatEnabled==FALSE )
		gosub BuggerOff
		Exit
	endif
	
	if ( g_hTarget!=NULL )
		if ( g_hTarget!=g_hObject )
			gosub BuggerOff
			Exit
		endif
	Endif

	g_bChatting = TRUE

	gosub LookForPersonOff

	Set g_hTarget, g_hObject
	Target g_hTarget, FALSE

	Trigger g_hTarget,LetsTalk

	gosub DisableWandering
	Stop
	SetIdle

	Wait SOCIALIZE_WAIT, 20, OnChatGiveUp

	Exit

;----------------------------------------------------------------
:OnGoodBye
;----------------------------------------------------------------

	;;DebugOut OnGoodBye

	GetTarget g_hTarget

	GetParam 0, g_hObject

	if ( g_hTarget!=g_hObject )
		Exit
	endif

	g_bChatting = FALSE

	gosub SetupNextChat
	gosub LeaveChat

	Exit

;----------------------------------------------------------------
:OnChatGiveUp
;
;	Give up waiting after sending / receiving the Hello message
;
;----------------------------------------------------------------

	;;DebugOut OnChatGiveUP	
	gosub CancelChat
	gosub SetupNextChat

	Exit

;----------------------------------------------------------------
:OnConverseDone
;----------------------------------------------------------------
	;;DebugOut OnConverseDone

	SetIdle

	if ( g_bChatting==TRUE )
		Trigger g_hTarget,YourTurn
	endif

	Exit


;----------------------------------------------------------------
:OnChatBegin
;
;	Stop and look at the guy who's talking to us...
;	
;----------------------------------------------------------------

	;;DebugOut OnChatBegin

	GetParam 0, g_hObject
	GetTarget g_hTarget

	if ( g_hTarget!=NULL )

		if ( g_hObject!=g_hTarget )
			Trigger g_hObject,LeaveMeAlone			
		Endif

	endif

	g_bChatting = TRUE

	gosub DisableWandering

	Stop
	SetIdle

	Set g_hTarget, g_hObject
	Target g_hTarget, FALSE

	FaceObject g_hTarget, 180

	Wait SOCIALIZE_WAIT, 0, DoNothing


	Exit

;----------------------------------------------------------------
:OnLookAtMe
;
;	p0 - who triggered us.
;
;	Useful for certain things....
;----------------------------------------------------------------
	
	GetParam 0, g_hObject

	IsMoving g_bTemp
	if ( g_bTemp==TRUE )
		Exit
	endif

	if ( g_hTarget!=NULL )
		if ( g_hTarget!=g_hObject )
			Exit
		endif
	endif

	FaceObject g_hObject, 180

	Exit

;----------------------------------------------------------------
:EndChat
;----------------------------------------------------------------

	;;DebugOut EndChat

	gosub CancelChat
	gosub SetupNextChat
	gosub LeaveChat

	Exit


;----------------------------------------------------------------
:LeaveChat
;----------------------------------------------------------------

	g_bChatting = FALSE

	GetFaceDir g_hMyObject, g_dirX, g_dirY, g_dirZ
	RotateDir g_dirX, g_dirY, g_dirZ, 180

	GetRandomFloat -45, 45, g_nRandom
	RotateDir g_dirX, g_dirY, g_dirZ, g_nRandom

	if( current_marker==NULL )
		FaceDir g_dirX, g_dirY, g_dirZ, 180, AboutFaceDone
	endif

	if( current_marker!=NULL )
		WalkTo current_marker, 0, OnGoToLocArrival
	endif

	Exit

;----------------------------------------------------------------
:AboutFaceDone
;----------------------------------------------------------------
	gosub BaseWanderGo
	Exit

;----------------------------------------------------------------
:OnChatArrival
;----------------------------------------------------------------
	Stop
	SetIdle
	Trigger g_hTarget,ChatBegin
	Converse -1, OnConverseDone

	GetRandomInt CHAT_MIN, CHAT_MAX, g_nRandom
	Wait SOCIALIZE_WAIT, g_nRandom, EndChat

	Exit


;----------------------------------------------------------------
:GoChat
;
;	Walk to our target and begin the chit-chat process....
;----------------------------------------------------------------

	Target g_hTarget, TRUE
	gosub DisableWandering
	WalkTo g_hTarget, 0, OnChatArrival

	g_bChatting = TRUE

	GetRandomFloat 4,10,g_nRandom

	Wait SOCIALIZE_WAIT, g_nRandom, OnChatGiveUp

	Exit

;----------------------------------------------------------------
:OnLetsTalk
;
;	p0 - handle of trigger sender...
;----------------------------------------------------------------
	GetParam 0, g_hObject

	if ( g_hObject!=g_hTarget )
		Trigger g_hObject,LeaveMeAlone
		Exit
	endif

	gosub GoChat

	Exit

;----------------------------------------------------------------
:OnLeaveMeAlone
;
;	p0 - handle of trigger sender...
;----------------------------------------------------------------
	GetParam 0, g_hObject

	if ( g_hObject!=g_hTarget )
		Exit
	endif

	Set g_hTarget, NULL
	Target NULL

	gosub SetupNextChat

	Exit

;----------------------------------------------------------------
:OnYourTurn
;
;	Play my anim and then tell them we're done...
;----------------------------------------------------------------

	if (g_bChatting==FALSE)
		Exit
	Endif

	Converse -1, OnConverseDone

	Exit

;----------------------------------------------------------------
:OnFoundTarget
;
;	p0 - hTarget
;----------------------------------------------------------------

	if ( g_bChatEnabled==FALSE )
		Exit
	endif

;	Set him as our target.
	if ( g_bSocializeEnabled==FALSE )
		EXIT
	endif

	GetParam 0, g_hTarget
	Target g_hTarget, FALSE

	gosub LookForPersonOff

	Trigger g_hTarget,Hello

	Wait SOCIALIZE_WAIT, 3, OnChatGiveUp
	
	Exit

;----------------------------------------------------------------
:LookForPersonOn
;----------------------------------------------------------------

	OnFoundTarget OnFoundTarget

; Figure out how long to wait for someone to show up...
	GetRandomInt MIN_CHAT_SEARCH, MAX_CHAT_SEARCH, g_nRandom
	Wait SOCIALIZE_WAIT, g_nRandom, SetupNextChat

	Exit

;----------------------------------------------------------------
:LookForPersonOff
;----------------------------------------------------------------

	OnFoundTarget
	
	Exit

;----------------------------------------------------------------
:SetupNextChat
;----------------------------------------------------------------

	Target NULL
	Set g_hTarget, NULL

	Stop
	SetIdle
	gosub EnableWandering
	gosub LookForPersonOff
	GetRandomInt MIN_SOCIALIZE_WAIT, MAX_SOCIALIZE_WAIT, g_nRandom
	Wait SOCIALIZE_WAIT, g_nRandom, LookForPersonOn

	Exit

;----------------------------------------------------------------
:OnUse
;
;	Let's cancel anything we were doing so we can chill with the
;	player...
;----------------------------------------------------------------

	GetParam 0, g_hObject

	GetFaceDir g_hMyObject,g_dirX,g_dirY,g_dirZ

	gosub DisableChat
	gosub DisableWandering

	Stop
	SetIdle

	g_hTarget = g_hObject
	Target g_hTarget, FALSE

	Exit FALSE

;----------------------------------------------------------------
:OnRUDEExit
;----------------------------------------------------------------
	Set g_hTarget, NULL
	Target NULL

	if( current_marker == NULL )
		gosub EnableWandering
		gosub EnableChat
		FaceDir g_dirX,g_dirY,g_dirZ,180
	else
		WalkTo current_marker, 0, OnGoToLocArrival
	endif

	Exit

;----------------------------------------------------------------
:Startup
;
;	Until level design does this for all NPCs, we'll just 
;	force all NPCs to do simple wander...
;
;----------------------------------------------------------------

;	if ( bWanderEnabled==FALSE )
;		gosub BaseWanderForceStartUp
;	endif

	if ( g_bSocializeEnabled==TRUE )
		if ( g_bChatEnabled==TRUE )
			gosub SetupNextChat
		endif
	endif

	Exit

;----------------------------------------------------------------
:OnDamage
;
;	store who hit us...
;	p0 = hAttacker
;	p1 = HitPoints
;	p2 = DamageType
;
;----------------------------------------------------------------

	if ( g_hTarget!=NULL )
		IsPlayer g_hTarget, g_bTemp
		if ( g_bTemp==TRUE )
			Exit
		Endif
	Endif

	Target NULL

	GetParam 0, g_hTarget
	Target g_hTarget, FALSE
	
	gosub RunAway
	
	Exit

;----------------------------------------------------------------
:OnDamageDone
;
;	Run Forest Run....
;
;----------------------------------------------------------------
	Exit


;----------------------------------------------------------------
:OnProjectile
;
;	Run for help!
;
;	p0	- hProjectile
;	p1	- hLaunchedFrom
;	p2	- dist
;	
;----------------------------------------------------------------

	if ( g_hTarget!=NULL )
		IsPlayer g_hTarget, g_bTemp
		if ( g_bTemp==TRUE )
			Exit
		Endif
	Endif

	Target NULL

	GetParam 1, g_hTarget
	Target g_hTarget, FALSE
	
	gosub RunAway
	
	Exit

;----------------------------------------------------------------
:RunAway
;
;
;
;----------------------------------------------------------------
	if ( g_hTarget==NULL )
		Exit
	endif

	OnProjectile

	gosub DisableWandering

	Stop
	SetIdle
;
; Cancel some timers...
;
	Wait SOCIALIZE_WAIT, 0, DoNothing

	gosub BaseRunAway

	Exit

;----------------------------------------------------------
:BaseRunCancel
;
;	We're overloading the function here....
;
;----------------------------------------------------------

	debugout NPCBase RUN Cancel!
	gosub BaseRunCancel,1

	Set g_hTarget, NULL
	Target NULL
	Stop

	gosub EnableWandering
	gosub EnableChat

	OnProjectile OnProjectile, 200

	Exit

;----------------------------------------------------------------
:BaseRunFindHidingPlace
;
; Overload this so we can find a guard...
;
;----------------------------------------------------------------
#numberArray		hGuardArray[5]
#number				nGuards = 0

#numberArray		hGuardTemp[5]
#numberArray		hGuardArray[5]
#number				nGuards = 0
#number				nValidGuards = 0
#number				guardX
#number				guardY
#number				guardZ

	gosub BaseRunFindHidingPlace, 1

	if ( g_hHidingPlace!=NULL )
		Exit
	endif

	GetObjects GuardBase, 1600, 5, hGuardTemp, nGuards

	if ( nGuards == 0 )
		Exit
	Endif

	g_nTemp = 0
	nValidGuards = 0

	GetPos g_hTarget,g_posX,g_posY,g_posZ

	while ( g_nTemp < nGuards )
		ArrayGet hGuardTemp, g_nTemp, g_hObject
		CanReachObject g_hObject, g_bTemp
		if ( g_bTemp==TRUE )

			GetPos g_hObject,guardX,guardY,guardZ

			VecDist guardX,guardY,guardZ,g_posX,g_posY,g_posZ,g_nTemp

			if ( g_nTemp > 500 )
				ArrayPut hGuardArray,nValidGuards,g_hObject
				Add nValidGuards,1
			endif
		Endif
		
		Add g_nTemp,1

	endwhile

	if ( nValidGuards>0 )
		Sub nValidGuards,1
		GetRandomInt 0,nValidGuards,g_nRandom
		ArrayGet hGuardArray,g_nRandom,g_hHidingPlace
		DebugOut Found Guard!  Set him as our hiding place....
		gosub BaseRunHide
		Exit
	Endif

	g_hHidingPlace = NULL

	Exit

;----------------------------------------------------------------
:BaseRunAway
;----------------------------------------------------------------

	if ( current_marker!=NULL )
		; If we're trying to runaway, just run to
		; our marker...
		Target NULL
		g_hTarget = NULL
		RunTo current_marker, 0, OnGoToLocArrival
		Exit
	Endif

#hobject	hTemp

	hTemp = g_hTarget

	gosub DisableWandering
	gosub DisableChat

	g_hTarget = hTemp
	Target g_hTarget,FALSE

	gosub BaseRunAway,1

	Exit

;----------------------------------------------------------------
:BaseWanderStartup
;----------------------------------------------------------------

	gosub BaseWanderStartup,1

	if ( bWanderEnabled==FALSE )
		g_bSocializeEnabled = FALSE
	endif

	if ( nWanderPathCount!=0 )
		g_bSocializeEnabled = FALSE
	Endif

	if ( nWanderLeash!=0 )
		g_bSocializeEnabled = FALSE
	Endif

	exit

;----------------------------------------------------------------
:NPCBaseInit
;----------------------------------------------------------------

	gosub BaseWanderInit
	Wait 0, 0.1, Startup

	AddTrigger Hello, OnHello
	AddTrigger LetsTalk, OnLetsTalk
	AddTrigger LeaveMeAlone, OnLeaveMeAlone
	AddTrigger GoodBye, OnGoodBye
	AddTrigger YourTurn, OnYourTurn
	AddTrigger LookAtMe, OnLookAtMe
	AddTrigger ChatBegin, OnChatBegin
	AddTrigger Use, OnUse
	AddTrigger GoToLoc, OnGoToLoc
	AddTrigger WarpToLoc, OnWarpToLoc

	OnRUDEExit OnRudeExit

	OnProjectile OnProjectile, 200
	OnDamageDone OnDamageDone
	OnDamage OnDamage

	Set g_bAskForHelp, TRUE
	; 100 feet...
	Set MIN_RUNAWAY_DIST, 1200

	AddFriend NPC
	AddFriend Player
	AddFriend GuardBase

	gosub BaseRunInit

	Exit

