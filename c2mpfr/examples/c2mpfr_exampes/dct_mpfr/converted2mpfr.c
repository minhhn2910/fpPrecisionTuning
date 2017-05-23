#include <stdio.h>
#include <mpfr.h>
#define LEN 23 
 int config_vals[LEN];
  mpfr_t workspace_temp_main;
  mpfr_t data_temp_main;
  mpfr_t tmp0_jpeg_fdct_float;
  mpfr_t tmp1_jpeg_fdct_float;
  mpfr_t tmp2_jpeg_fdct_float;
  mpfr_t tmp3_jpeg_fdct_float;
  mpfr_t tmp4_jpeg_fdct_float;
  mpfr_t tmp5_jpeg_fdct_float;
  mpfr_t tmp6_jpeg_fdct_float;
  mpfr_t tmp7_jpeg_fdct_float;
  mpfr_t tmp10_jpeg_fdct_float;
  mpfr_t tmp11_jpeg_fdct_float;
  mpfr_t tmp12_jpeg_fdct_float;
  mpfr_t tmp13_jpeg_fdct_float;
  mpfr_t z1_jpeg_fdct_float;
  mpfr_t z2_jpeg_fdct_float;
  mpfr_t z3_jpeg_fdct_float;
  mpfr_t z4_jpeg_fdct_float;
  mpfr_t z5_jpeg_fdct_float;
  mpfr_t z11_jpeg_fdct_float;
  mpfr_t z13_jpeg_fdct_float;
  mpfr_t data_temp_jpeg_fdct_float;
        mpfr_t temp_var_1;
        mpfr_t temp_var_2;
        mpfr_t temp_var_3;
        mpfr_t temp_var_4;
        mpfr_t temp_var_5;
        mpfr_t temp_var_6;
        mpfr_t temp_var_7;
        mpfr_t temp_var_8;
int init_mpfr() { 
  mpfr_init2(workspace_temp_main, config_vals[1]);
  mpfr_init2(data_temp_main, config_vals[2]);
  mpfr_init2(tmp0_jpeg_fdct_float, config_vals[3]);
  mpfr_init2(tmp1_jpeg_fdct_float, config_vals[4]);
  mpfr_init2(tmp2_jpeg_fdct_float, config_vals[5]);
  mpfr_init2(tmp3_jpeg_fdct_float, config_vals[6]);
  mpfr_init2(tmp4_jpeg_fdct_float, config_vals[7]);
  mpfr_init2(tmp5_jpeg_fdct_float, config_vals[8]);
  mpfr_init2(tmp6_jpeg_fdct_float, config_vals[9]);
  mpfr_init2(tmp7_jpeg_fdct_float, config_vals[10]);
  mpfr_init2(tmp10_jpeg_fdct_float, config_vals[11]);
  mpfr_init2(tmp11_jpeg_fdct_float, config_vals[12]);
  mpfr_init2(tmp12_jpeg_fdct_float, config_vals[13]);
  mpfr_init2(tmp13_jpeg_fdct_float, config_vals[14]);
  mpfr_init2(z1_jpeg_fdct_float, config_vals[15]);
  mpfr_init2(z2_jpeg_fdct_float, config_vals[16]);
  mpfr_init2(z3_jpeg_fdct_float, config_vals[17]);
  mpfr_init2(z4_jpeg_fdct_float, config_vals[18]);
  mpfr_init2(z5_jpeg_fdct_float, config_vals[19]);
  mpfr_init2(z11_jpeg_fdct_float, config_vals[20]);
  mpfr_init2(z13_jpeg_fdct_float, config_vals[21]);
  mpfr_init2(data_temp_jpeg_fdct_float, config_vals[22]);
        mpfr_init2 (temp_var_1, config_vals[0]);
        mpfr_init2 (temp_var_2, config_vals[0]);
        mpfr_init2 (temp_var_3, config_vals[0]);
        mpfr_init2 (temp_var_4, config_vals[0]);
        mpfr_init2 (temp_var_5, config_vals[0]);
        mpfr_init2 (temp_var_6, config_vals[0]);
        mpfr_init2 (temp_var_7, config_vals[0]);
        mpfr_init2 (temp_var_8, config_vals[0]);
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

void jpeg_fdct_float(float *);
float data[8][8] = {{139, 144, 149, 153, 155, 155, 155, 155}, {144, 151, 153, 156, 159, 156, 156, 156}, {150, 155, 160, 163, 158, 156, 156, 156}, {159, 161, 162, 160, 160, 159, 159, 159}, {159, 160, 161, 162, 162, 155, 155, 155}, {161, 161, 161, 161, 160, 157, 157, 157}, {162, 162, 161, 163, 162, 157, 157, 157}, {162, 162, 161, 161, 163, 158, 158, 158}};
float workspace[8][8];
int main(int argc, char *argv[])
{
 init_readconfig();
  int i;
  int j;
  int runs;
  for (runs = 0; runs < 10; runs++){
  {
    for (i = 0; i < 8; i++){
    {
      for (j = 0; j < 8; j++){
      {
        mpfr_set_d(data_temp_main, data[i][j], MPFR_RNDZ);
                        mpfr_sub_d(workspace_temp_main, data_temp_main, 128.0, MPFR_RNDZ);
        
workspace[i][j] = mpfr_get_d(workspace_temp_main, MPFR_RNDZ);
      }

            }

    }

        }

    jpeg_fdct_float((float *) workspace);
  }

    }

  for (i = 0; i < 8; i++){
  {
    for (j = 0; j < 8; j++){
    {
      printf("%.10f,", workspace[i][j]);
    }

        }

  }

    }

  exit(0);
}

void jpeg_fdct_float(float *data)
{
  float *dataptr;
  int ctr;
  dataptr = data;
  for (ctr = 8 - 1; ctr >= 0; ctr--){
  {
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[0], MPFR_RNDZ);
    mpfr_set(tmp0_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[7], MPFR_RNDZ);
            mpfr_add(tmp0_jpeg_fdct_float, tmp0_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[0], MPFR_RNDZ);
    mpfr_set(tmp7_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[7], MPFR_RNDZ);
            mpfr_sub(tmp7_jpeg_fdct_float, tmp7_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[1], MPFR_RNDZ);
    mpfr_set(tmp1_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[6], MPFR_RNDZ);
            mpfr_add(tmp1_jpeg_fdct_float, tmp1_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[1], MPFR_RNDZ);
    mpfr_set(tmp6_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[6], MPFR_RNDZ);
            mpfr_sub(tmp6_jpeg_fdct_float, tmp6_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[2], MPFR_RNDZ);
    mpfr_set(tmp2_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[5], MPFR_RNDZ);
            mpfr_add(tmp2_jpeg_fdct_float, tmp2_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[2], MPFR_RNDZ);
    mpfr_set(tmp5_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[5], MPFR_RNDZ);
            mpfr_sub(tmp5_jpeg_fdct_float, tmp5_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[3], MPFR_RNDZ);
    mpfr_set(tmp3_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[4], MPFR_RNDZ);
            mpfr_add(tmp3_jpeg_fdct_float, tmp3_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[3], MPFR_RNDZ);
    mpfr_set(tmp4_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[4], MPFR_RNDZ);
            mpfr_sub(tmp4_jpeg_fdct_float, tmp4_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp10_jpeg_fdct_float, tmp0_jpeg_fdct_float, tmp3_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(tmp13_jpeg_fdct_float, tmp0_jpeg_fdct_float, tmp3_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp11_jpeg_fdct_float, tmp1_jpeg_fdct_float, tmp2_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(tmp12_jpeg_fdct_float, tmp1_jpeg_fdct_float, tmp2_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(data_temp_jpeg_fdct_float, tmp10_jpeg_fdct_float, tmp11_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[0] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(data_temp_jpeg_fdct_float, tmp10_jpeg_fdct_float, tmp11_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[4] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
    
        mpfr_add(temp_var_1, tmp12_jpeg_fdct_float, tmp13_jpeg_fdct_float, MPFR_RNDZ);
        mpfr_mul_d(z1_jpeg_fdct_float, (temp_var_1), ((float) 0.707106781), MPFR_RNDZ);
            mpfr_add(data_temp_jpeg_fdct_float, tmp13_jpeg_fdct_float, z1_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[2] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(data_temp_jpeg_fdct_float, tmp13_jpeg_fdct_float, z1_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[6] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp10_jpeg_fdct_float, tmp4_jpeg_fdct_float, tmp5_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp11_jpeg_fdct_float, tmp5_jpeg_fdct_float, tmp6_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp12_jpeg_fdct_float, tmp6_jpeg_fdct_float, tmp7_jpeg_fdct_float, MPFR_RNDZ);
    
        mpfr_sub(temp_var_2, tmp10_jpeg_fdct_float, tmp12_jpeg_fdct_float, MPFR_RNDZ);
        mpfr_mul_d(z5_jpeg_fdct_float, (temp_var_2), ((float) 0.382683433), MPFR_RNDZ);
    
        mpfr_mul_d(temp_var_3, tmp10_jpeg_fdct_float, ((float) 0.541196100), MPFR_RNDZ);
        mpfr_add(z2_jpeg_fdct_float, (temp_var_3), z5_jpeg_fdct_float, MPFR_RNDZ);
    
        mpfr_mul_d(temp_var_4, tmp12_jpeg_fdct_float, ((float) 1.306562965), MPFR_RNDZ);
        mpfr_add(z4_jpeg_fdct_float, (temp_var_4), z5_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_mul_d(z3_jpeg_fdct_float, tmp11_jpeg_fdct_float, ((float) 0.707106781), MPFR_RNDZ);
            mpfr_add(z11_jpeg_fdct_float, tmp7_jpeg_fdct_float, z3_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(z13_jpeg_fdct_float, tmp7_jpeg_fdct_float, z3_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(data_temp_jpeg_fdct_float, z13_jpeg_fdct_float, z2_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[5] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(data_temp_jpeg_fdct_float, z13_jpeg_fdct_float, z2_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[3] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(data_temp_jpeg_fdct_float, z11_jpeg_fdct_float, z4_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[1] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(data_temp_jpeg_fdct_float, z11_jpeg_fdct_float, z4_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[7] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
    dataptr += 8;
  }

    }

  dataptr = data;
  for (ctr = 8 - 1; ctr >= 0; ctr--){
  {
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 0], MPFR_RNDZ);
    mpfr_set(tmp0_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 7], MPFR_RNDZ);
            mpfr_add(tmp0_jpeg_fdct_float, tmp0_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 0], MPFR_RNDZ);
    mpfr_set(tmp7_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 7], MPFR_RNDZ);
            mpfr_sub(tmp7_jpeg_fdct_float, tmp7_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 1], MPFR_RNDZ);
    mpfr_set(tmp1_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 6], MPFR_RNDZ);
            mpfr_add(tmp1_jpeg_fdct_float, tmp1_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 1], MPFR_RNDZ);
    mpfr_set(tmp6_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 6], MPFR_RNDZ);
            mpfr_sub(tmp6_jpeg_fdct_float, tmp6_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 2], MPFR_RNDZ);
    mpfr_set(tmp2_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 5], MPFR_RNDZ);
            mpfr_add(tmp2_jpeg_fdct_float, tmp2_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 2], MPFR_RNDZ);
    mpfr_set(tmp5_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 5], MPFR_RNDZ);
            mpfr_sub(tmp5_jpeg_fdct_float, tmp5_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 3], MPFR_RNDZ);
    mpfr_set(tmp3_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 4], MPFR_RNDZ);
            mpfr_add(tmp3_jpeg_fdct_float, tmp3_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 3], MPFR_RNDZ);
    mpfr_set(tmp4_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
    mpfr_set_d(data_temp_jpeg_fdct_float, dataptr[8 * 4], MPFR_RNDZ);
            mpfr_sub(tmp4_jpeg_fdct_float, tmp4_jpeg_fdct_float, data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp10_jpeg_fdct_float, tmp0_jpeg_fdct_float, tmp3_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(tmp13_jpeg_fdct_float, tmp0_jpeg_fdct_float, tmp3_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp11_jpeg_fdct_float, tmp1_jpeg_fdct_float, tmp2_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(tmp12_jpeg_fdct_float, tmp1_jpeg_fdct_float, tmp2_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(data_temp_jpeg_fdct_float, tmp10_jpeg_fdct_float, tmp11_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[8 * 0] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(data_temp_jpeg_fdct_float, tmp10_jpeg_fdct_float, tmp11_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[8 * 4] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
    
        mpfr_add(temp_var_5, tmp12_jpeg_fdct_float, tmp13_jpeg_fdct_float, MPFR_RNDZ);
        mpfr_mul_d(z1_jpeg_fdct_float, (temp_var_5), ((float) 0.707106781), MPFR_RNDZ);
            mpfr_add(data_temp_jpeg_fdct_float, tmp13_jpeg_fdct_float, z1_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[8 * 2] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(data_temp_jpeg_fdct_float, tmp13_jpeg_fdct_float, z1_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[8 * 6] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp10_jpeg_fdct_float, tmp4_jpeg_fdct_float, tmp5_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp11_jpeg_fdct_float, tmp5_jpeg_fdct_float, tmp6_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(tmp12_jpeg_fdct_float, tmp6_jpeg_fdct_float, tmp7_jpeg_fdct_float, MPFR_RNDZ);
    
        mpfr_sub(temp_var_6, tmp10_jpeg_fdct_float, tmp12_jpeg_fdct_float, MPFR_RNDZ);
        mpfr_mul_d(z5_jpeg_fdct_float, (temp_var_6), ((float) 0.382683433), MPFR_RNDZ);
    
        mpfr_mul_d(temp_var_7, tmp10_jpeg_fdct_float, ((float) 0.541196100), MPFR_RNDZ);
        mpfr_add(z2_jpeg_fdct_float, (temp_var_7), z5_jpeg_fdct_float, MPFR_RNDZ);
    
        mpfr_mul_d(temp_var_8, tmp12_jpeg_fdct_float, ((float) 1.306562965), MPFR_RNDZ);
        mpfr_add(z4_jpeg_fdct_float, (temp_var_8), z5_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_mul_d(z3_jpeg_fdct_float, tmp11_jpeg_fdct_float, ((float) 0.707106781), MPFR_RNDZ);
            mpfr_add(z11_jpeg_fdct_float, tmp7_jpeg_fdct_float, z3_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(z13_jpeg_fdct_float, tmp7_jpeg_fdct_float, z3_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(data_temp_jpeg_fdct_float, z13_jpeg_fdct_float, z2_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[8 * 5] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(data_temp_jpeg_fdct_float, z13_jpeg_fdct_float, z2_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[8 * 3] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_add(data_temp_jpeg_fdct_float, z11_jpeg_fdct_float, z4_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[8 * 1] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
            mpfr_sub(data_temp_jpeg_fdct_float, z11_jpeg_fdct_float, z4_jpeg_fdct_float, MPFR_RNDZ);
    
dataptr[8 * 7] = mpfr_get_d(data_temp_jpeg_fdct_float, MPFR_RNDZ);
    dataptr++;
  }

    }

}

//end of conversion, hopefully it will work :)