/**********************************************************************/
/*                                                                    */
/*                            File "smpl.h"                           */
/*  Includes, Defines, & Extern Declarations for Simulation Programs   */
/*                                                                    */
/*                                           (c) 1987  M. H. MacDougall */
/*                                                                    */
/**********************************************************************/

#include <stdio.h>
#include <math.h>

typedef double real;
#define then

extern real Lq(), U(), B(), time();
extern char *fname(), *mname();
extern FILE sendto();

extern real ranf(), uniform(), expntl(), erlang(), hyperx(), normal();
extern long seed();
