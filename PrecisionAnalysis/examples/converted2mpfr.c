#include <stdio.h>
#include <stdlib.h>
#include <mpfr.h>
#define LEN 5 
 int config_vals[LEN];
  mpfr_t a_main;
  mpfr_t b_main;
  mpfr_t c_main;
  mpfr_t d_main;
    mpfr_t temp_var_1;
int init_mpfr() { 
  mpfr_init2(a_main, config_vals[1]);
  mpfr_init2(b_main, config_vals[2]);
  mpfr_init2(c_main, config_vals[3]);
  mpfr_init2(d_main, config_vals[4]);
    mpfr_init2 (temp_var_1, config_vals[0]);
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

        fclose(myFile);
        init_mpfr();
        return 0;
}

int main(int argc, char *argv[])
{
 init_readconfig();
  if (argc > 1)
  {
    srand(atoi(argv[1]));
  }
  else
  {
    srand(5);
  }

  mpfr_set_d(a_main, ((double) rand()) / 2147483647, MPFR_RNDZ);
  mpfr_set_d(b_main, ((double) rand()) / 2147483647, MPFR_RNDZ);
  mpfr_set_d(c_main, ((double) rand()) / 2147483647, MPFR_RNDZ);
  
    mpfr_add(temp_var_1, a_main, b_main, MPFR_RNDZ);
    mpfr_mul(d_main, (temp_var_1), c_main, MPFR_RNDZ);
  printf("%.10f\n", mpfr_get_d(d_main, MPFR_RNDZ));
  return 0;
}

//end of conversion, hopefully it will work :)