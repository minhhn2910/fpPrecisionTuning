/**************************************************
* Chebyshev Approximation of a user defined real  *
* function FUNC(X) in double precision.           *
* ----------------------------------------------- *
* SAMPLE RUN:                                     *
* (Approximate sin(x) from x=0 to x=PI).          *
*                                                 *
* Chebyshev coefficients (N=10):                  *
*  0.94400243153647                               *
*  0.00000000000000                               *
* -0.49940325827041                               *
* -0.00000000000000                               *
*  0.02799207961755                               *
* -0.00000000000000                               *
* -0.00059669519580                               *
*  0.00000000000000                               *
*  0.00000670417552                               *
* -0.00000000000000                               *
*      X          Chebyshev Eval.     SIN(X)      *
*  -------------------------------------------    *
*  0.00000000       0.00000005      0.00000000    *
*  0.34906585       0.34202018      0.34202014    *
*  0.69813170       0.64278757      0.64278761    *
*  1.04719755       0.86602545      0.86602540    *
*  1.39626340       0.98480773      0.98480775    *
*  1.74532925       0.98480773      0.98480775    *
*  2.09439510       0.86602545      0.86602540    *
*  2.44346095       0.64278757      0.64278761    *
*  2.79252680       0.34202018      0.34202014    *
*  3.14159265       0.00000005      0.00000000    *
*                                                 *
*               C++ Release By J-P Moreau, Paris. *
*                      (www.jpmoreau.fr)          *
**************************************************/
// To link with Chebyshe.cpp
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#define  NMAX  51
#define  HALF  0.5
#define  TWO   2.0
#define  ZERO  0.0
#define  PI    4.0*atan(1.0)

#define  ONE   1.0
#define  QUART 0.25


    void   CHEBFT(double A,double B, double *C, int N);
    double CHEBEV(double A,double B, double *C, int M, double X);

    double X0,X1, COEFF[NMAX];
    double COEFF_temp;
    double DX, X;
    int I, N;

    // user defined function
    double FUNC(double x) {
      //~ return (sin(x));
      return (log(x+1));
    }

void main(int argc, char *argv[])
{
	if (argc < 2)
	{
			srand(256);
	}
	else 
	{
		srand(atoi(argv[1]));
	}
  //~ N=10;
  N=4;
  //~ X0=ZERO; X1=PI;
   X0=ZERO; X1=ONE;

  CHEBFT(X0,X1,COEFF,N);

  //~ printf(" Chebyshev coefficients (N=%d):\n", N);
  //~ for (I=1; I<=N; I++)
	//~ ;
    //~ printf(" %17.14f\n", COEFF[I]);

  DX=(X1-X0)/(N-1);
  X=X0-DX;

  //~ printf("      X        Chebyshev Eval.     SIN(X)    \n");
  //~ printf(" --------------------------------------------\n");
  for (I=1; I<=N; I++) {
    //~ X += DX;
    X = (float)rand()/RAND_MAX;
    printf("%11.8f %15.8f %15.8f\n", X, CHEBEV(X0,X1,COEFF,N,X), FUNC(X));
    //~ printf("%.14lf,", FUNC(X));
    //~ printf("%.14lf,", CHEBEV(X0,X1,COEFF,N,X));
  }
  

}

void CHEBFT(double A, double B, double *C, int N)  {
/*******************************************************
* Chebyshev fit: Given a real function FUNC(X), lower  *
* and upper limits of the interval [A,B] for X, and a  *
* maximum degree N, this routine computes the N Cheby- *
* shev coefficients Ck, such that FUNC(X) is approxima-*
* ted by:  N                                           *
*         [Sum Ck Tk-1(Y)] - C1/2, where X and Y are   *
*         k=1                                          *
* related by:     Y = (X - 1/2(A+B)) / (1/2(B-A))      *
* This routine is to be used with moderately large N   *
* (e.g. 30 or 50), the array of C's subsequently to be *
* truncated at the smaller value m such that Cm+1 and  *
* subsequent elements are negligible.                  *
*******************************************************/
  double A_temp, B_temp, C_temp;
  
  double SUM, F[NMAX];
  
  double F_temp;
  
  double BMA,BPA,FAC, Y;
  int J,K;
  
  A_temp = A;
  B_temp = B;
  
  //~ BMA=HALF*(B-A); BPA=HALF*(B+A);
  BMA=HALF*(B_temp-A_temp); BPA=HALF*(B_temp+A_temp);
  for (K=1; K<=N; K++) {
    Y=cos(PI*(K-HALF)/N);
    
    F_temp = FUNC(Y*BMA+BPA);
    F[K]= F_temp;
    //~ F[K]=FUNC(Y*BMA+BPA);
  }
  FAC=TWO/N;
  for (J=1; J<=N; J++) {
    SUM=ZERO;
    for (K=1; K<=N; K++){
		F_temp = F[K];
		SUM += F_temp*cos((PI*(J-1))*((K-HALF)/N));
      //~ SUM += F[K]*cos((PI*(J-1))*((K-HALF)/N));
	}
	C_temp = FAC*SUM;
	C[J] = C_temp; 
    //~ C[J]=FAC*SUM;
  }
}

double CHEBEV(double A, double B, double *C, int M, double X) {
/*********************************************************
* Chebyshev evaluation: All arguments are input. C is an *
* array of Chebyshev coefficients, of length M, the first*
* M elements of Coutput from subroutine CHEBFT (which    *
* must have been called with the same A and B). The Che- *
* byshev polynomial is evaluated at a point Y determined *
* from X, A and B, and the result FUNC(X) is returned as *
* the function value.                                    *
*********************************************************/
  double A_temp, B_temp, C_temp, X_temp;
  
  double D,DD,SV,Y,Y2;
  int J;
  
  A_temp = A;
  B_temp = B;
  X_temp = X;
  
  //~ if ((X-A)*(X-B) > ZERO) printf("\n X not in range.\n\n");
  
  D=ZERO; DD=ZERO;
  Y=(TWO*X_temp-A_temp-B_temp)/(B_temp-A_temp);  // change of variable
  //~ Y=(TWO*X-A-B)/(B-A);  // change of variable
  Y2=TWO*Y;
  for (J=M; J>1; J--) {
    SV=D;
    
    C_temp = C[J];
    D=Y2*D-DD+C_temp;
    //~ D=Y2*D-DD+C[J];
    
    DD=SV;
  }
  
  C_temp = C[1];
  return (Y*D-DD+HALF*C_temp);
  //~ return (Y*D-DD+HALF*C[1]);
}



// end of file Tchebysh.cpp
