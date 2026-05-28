;------------------------------------------------------------------
;	DarkP_initMyStuff.inc
;	Brett Yagi
;	11/09/2001
;
;	Initialization file for DarkP_bridgepuzzle.scr
;
;	Sequence to completion - ADCBDCBA
;
;-----------------------------------------------------


#numberArray 	aA[32]
#numberArray 	aB[32]
#numberArray 	aC[32]
#numberArray 	aD[32]

#numberArray 	aBridges[5]

;-----------------------------------------------
:InitializeStuff
;-----------------------------------------------

	ArrayPut aBridges 0 0
	ArrayPut aBridges 1 1
	ArrayPut aBridges 2 1
	ArrayPut aBridges 3 1
	ArrayPut aBridges 4 0

	ArrayPut aA  0 0
	ArrayPut aA  1 5
	ArrayPut aA  5 14
	ArrayPut aA  9 21
	ArrayPut aA 14 22
	ArrayPut aA 17 0
	ArrayPut aA 19 22
	ArrayPut aA 21 14
	ArrayPut aA 22 14
	ArrayPut aA 23 14
	ArrayPut aA 25 9
	ArrayPut aA 26 5
	ArrayPut aA 29 1
	ArrayPut aA 30 1
	ArrayPut aA 31 9

	ArrayPut aB  0 0
	ArrayPut aB  1 9
	ArrayPut aB  5 30
	ArrayPut aB  9 23
	ArrayPut aB 14 5
	ArrayPut aB 17 9
	ArrayPut aB 19 31
	ArrayPut aB 21 5
	ArrayPut aB 22 1
	ArrayPut aB 23 1
	ArrayPut aB 25 17
	ArrayPut aB 26 23
	ArrayPut aB 29 23
	ArrayPut aB 30 9
	ArrayPut aB 31 23

	ArrayPut aC  0 0
	ArrayPut aC  1 23
	ArrayPut aC  5 1
	ArrayPut aC  9 22
	ArrayPut aC 14 23
	ArrayPut aC 17 5
	ArrayPut aC 19 23
	ArrayPut aC 21 19
	ArrayPut aC 22 30
	ArrayPut aC 23 9
	ArrayPut aC 25 5
	ArrayPut aC 26 31
	ArrayPut aC 29 25
	ArrayPut aC 30 5
	ArrayPut aC 31 21

	ArrayPut aD  0 0
	ArrayPut aD  1 30
	ArrayPut aD  5 22
	ArrayPut aD  9 26
	ArrayPut aD 14 30
	ArrayPut aD 17 23
	ArrayPut aD 19 30
	ArrayPut aD 21 9
	ArrayPut aD 22 21
	ArrayPut aD 23 22
	ArrayPut aD 25 23
	ArrayPut aD 26 9
	ArrayPut aD 29 30
	ArrayPut aD 30 23
	ArrayPut aD 31 29
	
Exit 1
