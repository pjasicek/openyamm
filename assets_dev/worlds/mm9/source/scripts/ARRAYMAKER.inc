;--------------------------------
;	ArrayMaker.inc
;	by SJR
;	10-31-01
;	Purpose:manager for a list of lists of
;			associative strings and objects
;
;	Notes:
;		These must be set by the parent script
;		ARRAYNAME   = base name of item list
;		ARRAYFIRST  = index of first marker
;		ARRAYSIZE   = number of objects per root name
;		ARRAYSTRIDE = number of objects in one association
;
;--------------------------------
#include ListMaker.inc

#number		ARRAYNAME = 0
#number		ARRAYFIRST = 0
#number		ARRAYSIZE = 0
#number		ARRAYSTRIDE = 0

;--------------------------------
:InitArrayMaker
;--------------------------------
	LISTNAME = ARRAYNAME
	LISTFIRST = ARRAYFIRST
	LISTLAST = ARRAYSIZE * ARRAYSTRIDE
	Exit 1