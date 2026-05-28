;--------------------------------
;	ListMaker.inc
;	by SJR
;	10-31-01
;	Purpose:manager for a circular list of
;			strings\objects for use with
;			long marker paths etc
;	Notes:
;		These must be set by the parent script
;		LISTNAME = base name of item list
;		LISTFIRST= index of first marker
;		LISTLAST = index of last marker
;
;--------------------------------

;outputs
;contains the requested object
#hobject	LISTOBJECT = 0
;TRUE when at the ends of the list
#number		ARRIVEDLAST = 0
#number		ARRIVEDFIRST = 0
;index of objectname
#number		LISTINDEX = 0

;inputs
;base name of object list, ie Marker of Marker[x]
#string		LISTNAME = ""
;index of last one, ie 0 of Marker0
#number		LISTLAST = 0
;index of first one, ie 9 of Marker9
#number		LISTFIRST = 0

#string		FINALNAME = ""

;*** 4 steps (gosubs) on each of these ***
;1.	adjust index of string
;2.	check for ends of list
;3. make string name from index
;4. get hobject with above stringname

;--------------------------------
:GetLastObject
;	gets the object with the last index
;--------------------------------
	gosub list_SuffixMax
	gosub list_CheckPos
	gosub list_MakeName
	gosub list_MakeObject
	Exit 1

;--------------------------------
:GetFirstObject
;	gets the object with the first index
;--------------------------------
	gosub list_SuffixMin
	gosub list_CheckPos
	gosub list_MakeName
	gosub list_MakeObject
	Exit 1

;--------------------------------
:GetNextObject
;	gets the next object numerically
;--------------------------------
	gosub list_SuffixAdd
	gosub list_CheckPos
	gosub list_MakeName
	gosub list_MakeObject
	Exit 1

;--------------------------------
:GetPreviousObject
;	gets the previous object numerically
;--------------------------------
	gosub list_SuffixSub
	gosub list_CheckPos
	gosub list_MakeName
	gosub list_MakeObject
	Exit 1

;--------------------------------
:GetCurrentObject
;	gets the current object numerically
;	used for manually setting LISTINDEX
;	and for changing between lists
;--------------------------------
	gosub list_MakeName
	gosub list_MakeObject
	Exit 1

;********************************************
;private
;	keep out! do not screw with these.
;********************************************

:list_SuffixMin
	LISTINDEX = LISTFIRST
	Exit 1

:list_SuffixMax
	LISTINDEX = LISTLAST
	Exit 1

:list_SuffixAdd
	if( LISTINDEX==LISTLAST )
		LISTINDEX = LISTFIRST
	else
		LISTINDEX = LISTINDEX + 1
	endif
	Exit 1

:list_SuffixSub
	if( LISTINDEX == 0 )
		LISTINDEX = LISTLAST
	else
		LISTINDEX = LISTINDEX - 1
	endif
	Exit 1

:list_MakeName
	FINALNAME = LISTNAME + LISTINDEX
	Exit 1

:list_MakeObject
	GetObjectHandle FINALNAME, LISTOBJECT
	if( LISTOBJECT==0 )
;;		cprint "ListMaker.inc retrieved NULL handle for:"
;;		cprint FINALNAME
	endif
	Exit 1

:list_CheckPos
	ARRIVEDLAST  = 0
	ARRIVEDFIRST = 0
	if( LISTINDEX==LISTLAST )
		ARRIVEDLAST  = 1
	endif
	if( LISTINDEX==LISTFIRST )
		ARRIVEDFIRST = 1
	endif
	Exit 1