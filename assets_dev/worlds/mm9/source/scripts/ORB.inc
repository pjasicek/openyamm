;--------------------------------------------------
;Orb.scr
; timmy
; handles checking to see if the party got 6 orbs of linking.
;

;--------------------------------------------------

#include globals.inc



#Number					BeenDone
#Number					counter
#NumberArray			OrbArray[6]
#Number					GiveOrb
#Number					NoDice=0

;--------------------------------------------------
:reward
;--------------------------------------------------
;****************
;gives reward for uniting the clans
;****************


haskey 330 g_ntemp
if (g_ntemp==0, )
	givekey 330

	set BeenDone 1
	exit
endif
exit

;--------------------------------------------------
:Orb
;--------------------------------------------------

set NoDice, 0

	haskey 330, g_ntemp
	if (g_ntemp==0, )
		
		haskey 323 g_ntemp
		if (g_ntemp==1, )
			ArrayPut OrbArray, 0, 1
		else
			add NoDice 1
		endif
		
		haskey 324 g_ntemp
		if (g_ntemp==1, )
			ArrayPut OrbArray, 1, 1
		else
			add NoDice 1
		endif

		haskey 325 g_ntemp
		if (g_ntemp==1, )
			ArrayPut OrbArray, 2, 1
		else
			add NoDice 1
		endif

		haskey 326 g_ntemp
		if (g_ntemp==1, )
			ArrayPut OrbArray, 3, 1
		else
			add NoDice 1
		endif

		haskey 327 g_ntemp
		if (g_ntemp==1, )
			ArrayPut OrbArray, 4, 1
		else
			add NoDice 1
		endif

		haskey 328 g_ntemp
		if (g_ntemp==1, )
			ArrayPut OrbArray, 5, 1
		else
			add NoDice 1
		endif

		haskey 329 g_ntemp
		if (g_ntemp==1, )
			ArrayPut OrbArray, 6, 1
		else
			add NoDice 1
		endif
	endif

gosub CheckAllorb
exit

;--------------------------------------------------
:CheckAllorb
;--------------------------------------------------

if (NODice>=2)
	exit
endif
	

if ( BeenDone==1 )
    exit
endif

Set counter, 0



;--------------------------------------------------
:CheckAllOrbloop
;--------------------------------------------------



ArrayGet OrbArray, counter, GiveOrb
	if (GiveOrb==false)
		endif

Add Counter, 1

If (counter<6)
	Goto CheckAllOrbloop
endif


;...........success.............

gosub reward
exit