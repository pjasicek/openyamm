;----------------------------------------------------------------
; PoliceMan.Inc
; Jeff Leggett
; 08/22/2001
;
;	Behavior
;
;		- Don't attack anyone unless someone calls for help
;		
;		- If we get a call for help, if we have a path to
;		the target, then we'll go after it. Otherwise, we
;		won't...
;
;		- Just run the wander script until someone needs us.
;		(or attacks us!)
;
;----------------------------------------------------------------

#include basemelee.inc

;
;	Max # of times we'll let the player hit us before we get pissed...
;
#number			MAX_PLAYER_HIT_TOLERATION=3
#number			playerHitCount=0

;--------------------------------------------------------
:SetupTarget
;--------------------------------------------------------
	gosub SetupTarget,1

	IsPlayer g_hTarget, g_bTemp

	if ( g_bTemp==TRUE )
		AddEnemy Player
	Endif

	Exit

;----------------------------------------------------------------
:PoliceAlert
;
;  Make sure it's not a monster alert.  We don't protect monsters...
;
;	p0	- Handle of AI who sent the alert
;	p1	- Handle of that AI's target
;
;----------------------------------------------------------------

	GetParam 0, g_hObject

	GetStat g_hObject,IsMonster,g_bTemp

	if ( g_bTemp==TRUE )
		Exit
	endif

	IsClass g_hObject,GuardBase,g_bTemp

	if (g_bTemp==TRUE)

		; if a fellow guard is alerting me to this guy, then
		; he's an enemy now...
		GetParam 1, g_hObject

		IsFriend g_hObject,g_bTemp
		if ( g_bTemp==TRUE )
			GetClassName g_hObject,g_sTemp
			AddEnemy g_sTemp
		endif
	endif


	gosub OnAlert

	Exit

;----------------------------------------------------------------
:OnHelp
;
;	Help is different then Alert.  If the call for help, then
;	we'll see
;
;	Todo: Do more extensive checks...
;
;----------------------------------------------------------------

;
;	Make who ever they are yelping about an enemy..
;	
	GetParam 0, g_hObject

	IsFriend g_hObject,g_bTemp

	if ( g_bTemp==TRUE )
		; a friend says to hate this guy, so lets hate 'em...
		GetParam 1, g_hObject
		IsFriend g_hObject,g_bTemp
		if (g_bTemp==TRUE)
			GetClassName g_hObject,g_sTemp
			RemoveFriend g_sTemp
			AddEnemy g_sTemp
		endif
	endif

	gosub OnHelp,1

	Exit

;----------------------------------------------------------------
:OnDamage
;----------------------------------------------------------------

	GetParam 0, g_hObject

	IsPlayer g_hObject, g_bTemp

	if ( g_bTemp==TRUE )
		; If a player hits us too much, they are no longer a friend!
		Add playerHitCount,1

		if ( playerHitCount==MAX_PLAYER_HIT_TOLERATION )
			AddEnemy Player
		endif
	endif

	gosub OnDamage, 1

	Exit

;----------------------------------------------------------------
:PoliceManInit
;----------------------------------------------------------------

	gosub BaseInit

	OnAlert PoliceAlert
	OnHelp OnHelp
;;	gosub BaseWanderForceStartUp

	RemoveEnemy NPC

;
;	Guards don't like monsters....
;
	AddEnemy AIBase

	AddFriend Player
	AddFriend Cat
	AddFriend NPC
	AddFriend Animal
	AddFriend GuardBase

	exit



