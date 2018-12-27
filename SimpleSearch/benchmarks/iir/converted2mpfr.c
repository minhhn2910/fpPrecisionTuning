#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <mpfr.h>
#define INPUT_LEN 1000
#define LEN 6 
 int config_vals[LEN];
mpfr_t ydly;
  mpfr_t X_in_iir;
  mpfr_t yout_iir;
  mpfr_t coeff_iir;
    mpfr_t temp_var_1;
  mpfr_t out_main;
int init_mpfr() { 
mpfr_init2(ydly, config_vals[1]);
  mpfr_init2(X_in_iir, config_vals[2]);
  mpfr_init2(yout_iir, config_vals[3]);
  mpfr_init2(coeff_iir, config_vals[4]);
    mpfr_init2 (temp_var_1, config_vals[0]);
  mpfr_init2(out_main, config_vals[5]);
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
        for (s = 0; s < LEN; s++) {
            fscanf(myFile, "%d,", &config_vals[s]);
                          }
	//	config_vals[0] = 53; //all temp_vars are 53 bits in mantissa
        fclose(myFile);
        init_mpfr();
        return 0;             
}


float iir()
{
  int i;
  mpfr_set_d(coeff_iir, 0.9, MPFR_RNDZ);
  mpfr_set_d(X_in_iir, ((float)(rand()-RAND_MAX/2)/(float)(RAND_MAX/2)), MPFR_RNDZ);
 //  printf("%f, \n", mpfr_get_d(X_in_iir, MPFR_RNDZ));
    mpfr_mul(temp_var_1, coeff_iir, ydly, MPFR_RNDZ);
    mpfr_add(yout_iir, (temp_var_1), X_in_iir, MPFR_RNDZ);
  mpfr_set(ydly, yout_iir, MPFR_RNDZ);
  return mpfr_get_d(yout_iir, MPFR_RNDZ);
}

int main(int argc, char **argv)
{
 init_readconfig();
mpfr_set_d(ydly, 0.0, MPFR_RNDZ);
  int i;
  //~ srand(1);
    	if (argc < 2)
	{
			srand(1);
	}
	else 
	{
		srand(atoi(argv[1]));
	}
  
  for (i = 1; i < INPUT_LEN; i++){
  {
    mpfr_set_d(out_main, iir(), MPFR_RNDZ);
    printf("%f,", mpfr_get_d(out_main, MPFR_RNDZ));
  }

    }

  return 0;
}

//end of conversion, hopefully it will work :)
