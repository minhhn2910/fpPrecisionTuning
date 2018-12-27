#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <mpfr.h>
#define LEN 24 
 int config_vals[LEN];
mpfr_t X0;
mpfr_t X1;
mpfr_t COEFF_temp;
mpfr_t DX;
mpfr_t X;
    mpfr_t temp_var_1;
    mpfr_t temp_var_2;
    mpfr_t temp_var_3;
  mpfr_t A_temp_CHEBFT;
  mpfr_t B_temp_CHEBFT;
  mpfr_t C_temp_CHEBFT;
  mpfr_t SUM_CHEBFT;
  mpfr_t F_temp_CHEBFT;
  mpfr_t BMA_CHEBFT;
  mpfr_t BPA_CHEBFT;
  mpfr_t FAC_CHEBFT;
  mpfr_t Y_CHEBFT;
    mpfr_t temp_var_4;
    mpfr_t temp_var_5;
        mpfr_t temp_var_6;
        mpfr_t temp_var_7;
        mpfr_t temp_var_8;
    mpfr_t temp_var_9;
            mpfr_t temp_var_10;
            mpfr_t temp_var_11;
            mpfr_t temp_var_12;
            mpfr_t temp_var_13;
  mpfr_t A_temp_CHEBEV;
  mpfr_t B_temp_CHEBEV;
  mpfr_t C_temp_CHEBEV;
  mpfr_t X_temp_CHEBEV;
  mpfr_t D_CHEBEV;
  mpfr_t DD_CHEBEV;
  mpfr_t SV_CHEBEV;
  mpfr_t Y_CHEBEV;
  mpfr_t Y2_CHEBEV;
    mpfr_t temp_var_14;
    mpfr_t temp_var_15;
    mpfr_t temp_var_16;
    mpfr_t temp_var_17;
        mpfr_t temp_var_18;
        mpfr_t temp_var_19;
    mpfr_t temp_var_20;
    mpfr_t temp_var_21;
    mpfr_t temp_var_22;
    mpfr_t temp_var_23;
int init_mpfr() { 
mpfr_init2(X0, config_vals[1]);
mpfr_init2(X1, config_vals[2]);
mpfr_init2(COEFF_temp, config_vals[3]);
mpfr_init2(DX, config_vals[4]);
mpfr_init2(X, config_vals[5]);
    mpfr_init2 (temp_var_1, config_vals[0]);
    mpfr_init2 (temp_var_2, config_vals[0]);
    mpfr_init2 (temp_var_3, config_vals[0]);
  mpfr_init2(A_temp_CHEBFT, config_vals[6]);
  mpfr_init2(B_temp_CHEBFT, config_vals[7]);
  mpfr_init2(C_temp_CHEBFT, config_vals[8]);
  mpfr_init2(SUM_CHEBFT, config_vals[9]);
  mpfr_init2(F_temp_CHEBFT, config_vals[10]);
  mpfr_init2(BMA_CHEBFT, config_vals[11]);
  mpfr_init2(BPA_CHEBFT, config_vals[12]);
  mpfr_init2(FAC_CHEBFT, config_vals[13]);
  mpfr_init2(Y_CHEBFT, config_vals[14]);
    mpfr_init2 (temp_var_4, config_vals[0]);
    mpfr_init2 (temp_var_5, config_vals[0]);
        mpfr_init2 (temp_var_6, config_vals[0]);
        mpfr_init2 (temp_var_7, config_vals[0]);
        mpfr_init2 (temp_var_8, config_vals[0]);
    mpfr_init2 (temp_var_9, config_vals[0]);
            mpfr_init2 (temp_var_10, config_vals[0]);
            mpfr_init2 (temp_var_11, config_vals[0]);
            mpfr_init2 (temp_var_12, config_vals[0]);
            mpfr_init2 (temp_var_13, config_vals[0]);
  mpfr_init2(A_temp_CHEBEV, config_vals[15]);
  mpfr_init2(B_temp_CHEBEV, config_vals[16]);
  mpfr_init2(C_temp_CHEBEV, config_vals[17]);
  mpfr_init2(X_temp_CHEBEV, config_vals[18]);
  mpfr_init2(D_CHEBEV, config_vals[19]);
  mpfr_init2(DD_CHEBEV, config_vals[20]);
  mpfr_init2(SV_CHEBEV, config_vals[21]);
  mpfr_init2(Y_CHEBEV, config_vals[22]);
  mpfr_init2(Y2_CHEBEV, config_vals[23]);
    mpfr_init2 (temp_var_14, config_vals[0]);
    mpfr_init2 (temp_var_15, config_vals[0]);
    mpfr_init2 (temp_var_16, config_vals[0]);
    mpfr_init2 (temp_var_17, config_vals[0]);
        mpfr_init2 (temp_var_18, config_vals[0]);
        mpfr_init2 (temp_var_19, config_vals[0]);
    mpfr_init2 (temp_var_20, config_vals[0]);
    mpfr_init2 (temp_var_21, config_vals[0]);
    mpfr_init2 (temp_var_22, config_vals[0]);
    mpfr_init2 (temp_var_23, config_vals[0]);
}

int init_readconfig() {

  // For reading precision contents of config_file into array
   FILE *myFile;
     myFile = fopen("config_file.txt", "r");
 
        if (myFile == NULL) {
					printf("Error Reading File\n");
                exit (0);
                }
 
        int s;
        for (s = 0; s < LEN-1; s++) {
            fscanf(myFile, "%d,", &config_vals[s+1]);
                          }
		config_vals[0] = 53; //all temp_vars are 53 bits in mantissa
        fclose(myFile);
        init_mpfr();
        return 0;             
}

void CHEBFT(double A, double B, double *C, int N);
double CHEBEV(double A, double B, double *C, int M, double X);
double COEFF[51];
int I;
int N;
double FUNC(double x)
{
  //~ return sin(x);
  return log(1+x);
}

void main(int argc, char *argv[])
{
	//~ if (argc < 2)
	//~ {
			//~ srand(256);
	//~ }
	//~ else 
	//~ {
		//~ srand(atoi(argv[1]));
	//~ }

srand(256);
	
 init_readconfig();
 N = 4;
  //~ N = 10;
  mpfr_set_d(X0, 0.0, MPFR_RNDZ);
  mpfr_set_d(X1, 4.0 * atan(1.0), MPFR_RNDZ);
  CHEBFT(mpfr_get_d(X0,MPFR_RNDZ), mpfr_get_d(X1,MPFR_RNDZ), COEFF, N);
  

    mpfr_sub(temp_var_2, X1, X0, MPFR_RNDZ);

    mpfr_div_d(DX, (temp_var_2), (N - 1), MPFR_RNDZ);
      mpfr_sub(X, X0, DX, MPFR_RNDZ);
  for (I = 1; I <= N; I++){
  {
        //~ mpfr_add(X, X, DX, MPFR_RNDZ);
        mpfr_set_d(X, (float)rand()/RAND_MAX, MPFR_RNDZ);
    printf("%.14lf,", CHEBEV(mpfr_get_d(X0,MPFR_RNDZ), mpfr_get_d(X1,MPFR_RNDZ), COEFF, N, mpfr_get_d(X,MPFR_RNDZ)));
  }

    }

}

void CHEBFT(double A, double B, double *C, int N)
{
  double F[51];
  int J;
  int K;
  mpfr_set_d(A_temp_CHEBFT, A, MPFR_RNDZ);
  mpfr_set_d(B_temp_CHEBFT, B, MPFR_RNDZ);
  
    mpfr_sub(temp_var_4, B_temp_CHEBFT, A_temp_CHEBFT, MPFR_RNDZ);
    mpfr_mul_d(BMA_CHEBFT, (temp_var_4), 0.5, MPFR_RNDZ);
  
    mpfr_add(temp_var_5, B_temp_CHEBFT, A_temp_CHEBFT, MPFR_RNDZ);
    mpfr_mul_d(BPA_CHEBFT, (temp_var_5), 0.5, MPFR_RNDZ);
  for (K = 1; K <= N; K++){
  {
    mpfr_set_d(Y_CHEBFT, cos(((4.0 * atan(1.0)) * (K - 0.5)) / N), MPFR_RNDZ);
    mpfr_set_d(F_temp_CHEBFT, FUNC((mpfr_get_d(Y_CHEBFT, MPFR_RNDZ) * mpfr_get_d(BMA_CHEBFT, MPFR_RNDZ)) + mpfr_get_d(BPA_CHEBFT, MPFR_RNDZ)), MPFR_RNDZ);
    



F[K] = mpfr_get_d(F_temp_CHEBFT, MPFR_RNDZ);
  }

    }

  mpfr_set_d(FAC_CHEBFT, 2.0 / N, MPFR_RNDZ);
  for (J = 1; J <= N; J++){
  {
    mpfr_set_d(SUM_CHEBFT, 0.0, MPFR_RNDZ);
    for (K = 1; K <= N; K++){
    {
      mpfr_set_d(F_temp_CHEBFT, F[K], MPFR_RNDZ);
      




            mpfr_mul_d(temp_var_13, F_temp_CHEBFT, cos(((4.0 * atan(1.0)) * (J - 1)) * ((K - 0.5) / N)), MPFR_RNDZ);
      mpfr_add(SUM_CHEBFT, SUM_CHEBFT, temp_var_13, MPFR_RNDZ);
    }

        }

            mpfr_mul(C_temp_CHEBFT, FAC_CHEBFT, SUM_CHEBFT, MPFR_RNDZ);
    
C[J] = mpfr_get_d(C_temp_CHEBFT, MPFR_RNDZ);
  }

    }

}

double CHEBEV(double A, double B, double *C, int M, double X)
{
  int J;
  mpfr_set_d(A_temp_CHEBEV, A, MPFR_RNDZ);
  mpfr_set_d(B_temp_CHEBEV, B, MPFR_RNDZ);
  mpfr_set_d(X_temp_CHEBEV, X, MPFR_RNDZ);
  mpfr_set_d(D_CHEBEV, 0.0, MPFR_RNDZ);
  mpfr_set_d(DD_CHEBEV, 0.0, MPFR_RNDZ);
  
    mpfr_mul_d(temp_var_14, X_temp_CHEBEV, 2.0, MPFR_RNDZ);

    mpfr_sub(temp_var_15, (temp_var_14), A_temp_CHEBEV, MPFR_RNDZ);

    mpfr_sub(temp_var_16, (temp_var_15), B_temp_CHEBEV, MPFR_RNDZ);

    mpfr_sub(temp_var_17, B_temp_CHEBEV, A_temp_CHEBEV, MPFR_RNDZ);
    mpfr_div(Y_CHEBEV, (temp_var_16), (temp_var_17), MPFR_RNDZ);
      mpfr_mul_d(Y2_CHEBEV, Y_CHEBEV, 2.0, MPFR_RNDZ);
  for (J = M; J > 1; J--){
  {
    mpfr_set(SV_CHEBEV, D_CHEBEV, MPFR_RNDZ);
    mpfr_set_d(C_temp_CHEBEV, C[J], MPFR_RNDZ);
    
        mpfr_mul(temp_var_18, Y2_CHEBEV, D_CHEBEV, MPFR_RNDZ);

        mpfr_sub(temp_var_19, (temp_var_18), DD_CHEBEV, MPFR_RNDZ);
        mpfr_add(D_CHEBEV, (temp_var_19), C_temp_CHEBEV, MPFR_RNDZ);
    mpfr_set(DD_CHEBEV, SV_CHEBEV, MPFR_RNDZ);
  }

    }

  mpfr_set_d(C_temp_CHEBEV, C[1], MPFR_RNDZ);
  //output_stack != null, dump all itermediate operations here

    mpfr_mul(temp_var_20, Y_CHEBEV, D_CHEBEV, MPFR_RNDZ);

    mpfr_sub(temp_var_21, (temp_var_20), DD_CHEBEV, MPFR_RNDZ);

    mpfr_mul_d(temp_var_22, C_temp_CHEBEV, 0.5, MPFR_RNDZ);

    mpfr_add(temp_var_23, (temp_var_21), (temp_var_22), MPFR_RNDZ);
return mpfr_get_d(temp_var_23, MPFR_RNDZ);
}

//end of conversion, hopefully it will work :)
