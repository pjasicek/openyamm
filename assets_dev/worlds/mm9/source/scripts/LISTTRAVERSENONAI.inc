;------------------------------------------------------------------------------------------
;	ListTraverseNONAI.inc
;	by SJR
;	11-02-01
;	Advantages:
;			Traverses arbitrary list of markers.
;			Performs user callback at each marker.
;
;	Notes: (* default)
;
;	*	SetTraverseOnce = gosub this for one way traversal (ex 0,1,2,3)
;		SetTraverseLoop = gosub this for circular traversal (ex 0,1,2,3,0,1,2,3...)
;		SetTraversePace = gosub this for back and forth (ex 0,1,2,3,2,1,0...)
;
;		LISTNAME = base name of item list (ex "MyMarker" for MyMarker0,1,2...)
;		LISTFIRST= index of first marker of your path (ex 5 for path MyMarker5->MyMarker9)
;		LISTLAST = index of last marker of your path (ex 9 for path MyMarker5->MyMarker9)
;
;		Script will call "OnTraverseDone" at each marker. Override it.
;		Check the number LISTINDEX in OnTraverseDone to decide what to do.
;------------------------------------------------------------------------------------------
#include Flags.inc
#include ListMaker.inc

;inputs
;bool for looping path
#number		TRAVERSELOOP = 0
;bool for back and forth
#number		TRAVERSEPACE = 0
;bool for back and forth
#number		TRAVERSE_SPEED = 0

;bool for direction
#number		bForward = 1
;bool for active
#number		bContinue = 0
;bool for pause state
#number		bPaused = 0

#hobject		traverse_hMe = 0
#number			traverse_nTemp = 0

;----------------
:TraverseBegin
;	starts moving to first object,
;	sets up collision handling
;----------------
	GetMyHandle traverse_hMe

	if( LISTFIRST>LISTLAST )
		;;if user reversed indexes, switch back
		traverse_nTemp = LISTFIRST
		LISTFIRST = LISTLAST
		LISTLAST = traverse_nTemp
	endif
	bContinue = 1
	LISTINDEX = LISTLAST
	gosub traverse_GoToNext
	Exit 1

;----------------
:TraversePause
;	pauses path, remembers place
;----------------
	bPaused = 1
	Stop
	Exit 1

;----------------
:TraverseResume
;	resumes path where left off
;----------------
	bPaused = 0
	gosub traverse_Traverse
	gosub traverse_CheckLocation
	Exit 1

;----------------
:ReversePath
;	reverses direction of path
;----------------
	bForward = 1 - bForward
	Exit 1

;----------------
:OnTraverseDone
;	override this to do things
;	on the way, called at every marker
;----------------
	Exit 1

;----------------
:SetTraverseLoop
;	loop pathing until user stop
;----------------
	TRAVERSELOOP = 1
	TRAVERSEPACE = 0
	Exit 1

;----------------
:SetTraversePace
;	back and forth until user stop
;----------------
	TRAVERSELOOP = 0
	TRAVERSEPACE = 1
	Exit 1

;----------------
:SetTraverseOnce
;	do one trip at a time
;----------------
	TRAVERSELOOP = 0
	TRAVERSEPACE = 0
	Exit 1

;***************************************************
;private
;***************************************************
#number		traverse_x = 0
#number		traverse_y = 0
#number		traverse_z = 0

:traverse_GoToNext
	if( bContinue==0 )
		Exit 1
	endif
	if( bForward==1 )
		gosub GetNextObject
	else
		gosub GetPreviousObject
	endif
	if( bPaused==0 )
		gosub traverse_Traverse
		gosub traverse_CheckLocation
	endif
	Exit 1

:traverse_Traverse
	GetPOS LISTOBJECT, traverse_x,traverse_y,traverse_z
	MoveToPOS traverse_x,traverse_y,traverse_z, TRAVERSE_SPEED, traverse_TraverseTick
	Exit 1

:traverse_TraverseTick
	gosub OnTraverseDone
	gosub traverse_GoToNext
	Exit 1

:traverse_CheckLocation
	bContinue = 1
	if( TRAVERSELOOP==1 )
		Exit 1
	endif
	if( ARRIVEDLAST==1 )
		if( bForward==1 )
			bContinue = TRAVERSELOOP + TRAVERSEPACE
		endif
		bForward = 0
	endif
	if( ARRIVEDFIRST==1 )
		if( bForward==0 )
			bContinue = TRAVERSELOOP + TRAVERSEPACE
		endif
		bForward = 1
	endif
	Exit 1
