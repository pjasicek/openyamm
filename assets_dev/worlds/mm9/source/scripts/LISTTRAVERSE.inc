;------------------------------------------------------------------------------------------
;	ListTraverse.inc
;	by SJR
;	11-02-01
;	Advantages:
;			Traverses arbitrary list of markers.
;			Performs user callback at each marker.
;			Handles doors easily.
;
;	Notes: (* default)
;
;	*	SetTraverseWalk = gosub this for walking
;		SetTraverseRun  = gosub this for running
;	*	SetTraverseOnce = gosub this for one way traversal (ex 0,1,2,3)
;		SetTraverseLoop = gosub this for circular traversal (ex 0,1,2,3,0,1,2,3...)
;		SetTraversePace = gosub this for back and forth (ex 0,1,2,3,2,1,0...)
;	*	SetTraverseDefaults = gosub this to restore defaults
;
;		LISTNAME = base name of item list (ex "MyMarker" for MyMarker0,1,2...)
;		LISTFIRST= index of first marker of your path (ex 5 for path MyMarker5->MyMarker9)
;		LISTLAST = index of last marker of your path (ex 9 for path MyMarker5->MyMarker9)
;
;		Script will call "OnTraverseDone" at each marker. Override it.
;		Check the number LISTINDEX in OnTraverseDone to decide what to do.
;		Change 'TRAVERSERADIUS' to a suitable Walk\Run radius (defaults to 40)
;------------------------------------------------------------------------------------------

#include ListMaker.inc

;inputs
;bool for run
#number		TRAVERSERUN = 0
;bool for looping path
#number		TRAVERSELOOP = 0
;bool for back and forth
#number		TRAVERSEPACE = 0
;radius of runto, walkto
#number		TRAVERSERADIUS = 40

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
;	starts walk\running from first object,
;	sets up door handling
;----------------
	GetMyHandle traverse_hMe
	OnDoor	traverse_TraverseDoor
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
:SetTraverseRun
;	enable running
;----------------
	TRAVERSERUN = 1
	Exit 1

;----------------
:SetTraverseWalk
;	disable running
;----------------
	TRAVERSERUN = 0
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

;----------------
:SetTraverseDefaults
;	restore all the defaults
;----------------
	TRAVERSELOOP = 0
	TRAVERSEPACE = 0
	TRAVERSERADIUS = 40
	TRAVERSERUN = 0
	Exit 1

;***************************************************
;private
;	keep out! do not screw with these.
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
	if( TRAVERSERUN==1 )
		RunTo LISTOBJECT, TRAVERSERADIUS, traverse_TraverseTick
	else
		WalkTo LISTOBJECT, TRAVERSERADIUS, traverse_TraverseTick
	endif
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

;;;Modified baseDoor.inc routine to cooperate(!) with this script

#hobject	traverse_hDoor = 0

#number		traverse_normalX = 0
#number		traverse_normalY = 0
#number		traverse_normalZ = 0

#number		traverse_velX = 0
#number		traverse_velY = 0
#number		traverse_velZ = 0
;--------------
:traverse_TraverseDoor
;--------------
	gosub TraversePause

	GetParam 0, traverse_hDoor
	GetStat traverse_hDoor,IsClosed,traverse_nTemp

	if ( traverse_nTemp==0 )
		gosub TraverseResume
		Exit 0
	endif

	GetParam 1, traverse_normalX
	GetParam 2, traverse_normalY
	GetParam 3, traverse_normalZ
	RotateDir traverse_normalX, traverse_normalY, traverse_normalZ, 180

	GetFaceDir traverse_hMe, traverse_velX, traverse_velY, traverse_velZ

	VecAngle traverse_normalX,0,traverse_normalZ,traverse_velX,0,traverse_velZ, traverse_nTemp
	if ( traverse_nTemp > 45 )
		exit 0
	endif
	Stop
	FaceDir traverse_normalX, 0, traverse_normalZ, 360
	Trigger traverse_hDoor, Use
	GetStat traverse_hDoor,DoorOpenTime,traverse_nTemp
	Wait 0, traverse_nTemp, TraverseResume

	Exit 1