#include <stdio.h>
#include <stdlib.h>
#include <mpfr.h>
#define LEN 23 
 int config_vals[LEN];
  mpfr_t temp_R16SRFFT;
  mpfr_t out0_R16SRFFT;
  mpfr_t out1_R16SRFFT;
  mpfr_t out2_R16SRFFT;
  mpfr_t out3_R16SRFFT;
  mpfr_t out4_R16SRFFT;
  mpfr_t out5_R16SRFFT;
  mpfr_t out6_R16SRFFT;
  mpfr_t out7_R16SRFFT;
  mpfr_t out8_R16SRFFT;
  mpfr_t out9_R16SRFFT;
  mpfr_t out10_R16SRFFT;
  mpfr_t out11_R16SRFFT;
  mpfr_t out12_R16SRFFT;
  mpfr_t out13_R16SRFFT;
  mpfr_t out14_R16SRFFT;
  mpfr_t out15_R16SRFFT;
  mpfr_t input_track_R16SRFFT;
  mpfr_t output_track_R16SRFFT;
    mpfr_t temp_var_1;
    mpfr_t temp_var_2;
    mpfr_t temp_var_3;
      mpfr_t temp_var_4 ;
      mpfr_t temp_var_5 ;
    mpfr_t temp_var_6;
    mpfr_t temp_var_7;
    mpfr_t temp_var_8;
    mpfr_t temp_var_9;
    mpfr_t temp_var_10;
    mpfr_t temp_var_11;
    mpfr_t temp_var_12;
    mpfr_t temp_var_13;
    mpfr_t temp_var_14;
    mpfr_t temp_var_15;
    mpfr_t temp_var_16;
    mpfr_t temp_var_17;
    mpfr_t temp_var_18;
    mpfr_t temp_var_19;
    mpfr_t temp_var_20;
      mpfr_t temp_var_21 ;
      mpfr_t temp_var_22 ;
    mpfr_t temp_var_23;
    mpfr_t temp_var_24;
  mpfr_t data_track_main;
  mpfr_t output_track_main;
  mpfr_t zero_main;
int init_mpfr() { 
  mpfr_init2(temp_R16SRFFT, config_vals[1]);
  mpfr_init2(out0_R16SRFFT, config_vals[2]);
  mpfr_init2(out1_R16SRFFT, config_vals[3]);
  mpfr_init2(out2_R16SRFFT, config_vals[4]);
  mpfr_init2(out3_R16SRFFT, config_vals[5]);
  mpfr_init2(out4_R16SRFFT, config_vals[6]);
  mpfr_init2(out5_R16SRFFT, config_vals[7]);
  mpfr_init2(out6_R16SRFFT, config_vals[8]);
  mpfr_init2(out7_R16SRFFT, config_vals[9]);
  mpfr_init2(out8_R16SRFFT, config_vals[10]);
  mpfr_init2(out9_R16SRFFT, config_vals[11]);
  mpfr_init2(out10_R16SRFFT, config_vals[12]);
  mpfr_init2(out11_R16SRFFT, config_vals[13]);
  mpfr_init2(out12_R16SRFFT, config_vals[14]);
  mpfr_init2(out13_R16SRFFT, config_vals[15]);
  mpfr_init2(out14_R16SRFFT, config_vals[16]);
  mpfr_init2(out15_R16SRFFT, config_vals[17]);
  mpfr_init2(input_track_R16SRFFT, config_vals[18]);
  mpfr_init2(output_track_R16SRFFT, config_vals[19]);
    mpfr_init2 (temp_var_1, config_vals[0]);
    mpfr_init2 (temp_var_2, config_vals[0]);
    mpfr_init2 (temp_var_3, config_vals[0]);
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
    mpfr_init2 (temp_var_24, config_vals[0]);
  mpfr_init2(data_track_main, config_vals[20]);
  mpfr_init2(output_track_main, config_vals[21]);
  mpfr_init2(zero_main, config_vals[22]);
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

void R16SRFFT(float input[16], float output[16])
{
  mpfr_set_d(input_track_R16SRFFT, input[0], MPFR_RNDN);
  mpfr_set(out0_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[8], MPFR_RNDN);
      mpfr_add(out0_R16SRFFT, out0_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[1], MPFR_RNDN);
  mpfr_set(out1_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[9], MPFR_RNDN);
      mpfr_add(out1_R16SRFFT, out1_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[2], MPFR_RNDN);
  mpfr_set(out2_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[10], MPFR_RNDN);
      mpfr_add(out2_R16SRFFT, out2_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[3], MPFR_RNDN);
  mpfr_set(out3_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[11], MPFR_RNDN);
      mpfr_add(out3_R16SRFFT, out3_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[4], MPFR_RNDN);
  mpfr_set(out4_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[12], MPFR_RNDN);
      mpfr_add(out4_R16SRFFT, out4_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[5], MPFR_RNDN);
  mpfr_set(out5_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[13], MPFR_RNDN);
      mpfr_add(out5_R16SRFFT, out5_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[6], MPFR_RNDN);
  mpfr_set(out6_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[14], MPFR_RNDN);
      mpfr_add(out6_R16SRFFT, out6_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[7], MPFR_RNDN);
  mpfr_set(out7_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[15], MPFR_RNDN);
      mpfr_add(out7_R16SRFFT, out7_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[0], MPFR_RNDN);
  mpfr_set(out8_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[8], MPFR_RNDN);
      mpfr_sub(out8_R16SRFFT, out8_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[1], MPFR_RNDN);
  mpfr_set(out9_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[9], MPFR_RNDN);
      mpfr_sub(out9_R16SRFFT, out9_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[2], MPFR_RNDN);
  mpfr_set(out10_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[10], MPFR_RNDN);
      mpfr_sub(out10_R16SRFFT, out10_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[3], MPFR_RNDN);
  mpfr_set(out11_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[11], MPFR_RNDN);
      mpfr_sub(out11_R16SRFFT, out11_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[12], MPFR_RNDN);
  mpfr_set(out12_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[4], MPFR_RNDN);
      mpfr_sub(out12_R16SRFFT, out12_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[13], MPFR_RNDN);
  mpfr_set(out13_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[5], MPFR_RNDN);
      mpfr_sub(out13_R16SRFFT, out13_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[14], MPFR_RNDN);
  mpfr_set(out14_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[6], MPFR_RNDN);
      mpfr_sub(out14_R16SRFFT, out14_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[15], MPFR_RNDN);
  mpfr_set(out15_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(input_track_R16SRFFT, input[7], MPFR_RNDN);
      mpfr_sub(out15_R16SRFFT, out15_R16SRFFT, input_track_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_1, out13_R16SRFFT, out9_R16SRFFT, MPFR_RNDN);
    mpfr_mul_d(temp_R16SRFFT, (temp_var_1), 0.38268343236508978, MPFR_RNDN);
  
    mpfr_mul_d(temp_var_2, out9_R16SRFFT, 1.30656296487637660, MPFR_RNDN);
    mpfr_add(out9_R16SRFFT, (temp_var_2), temp_R16SRFFT, MPFR_RNDN);
  
    mpfr_mul_d(temp_var_3, out13_R16SRFFT, 0.54119610014619690, MPFR_RNDN);
    mpfr_add(out13_R16SRFFT, (temp_var_3), temp_R16SRFFT, MPFR_RNDN);
    mpfr_set_d(temp_var_4, 0.707106781186547460, MPFR_RNDN);
    mpfr_mul_d(out14_R16SRFFT, out14_R16SRFFT, 0.707106781186547460, MPFR_RNDN);
    mpfr_set_d(temp_var_5, 0.707106781186547460, MPFR_RNDN);
    mpfr_mul_d(out10_R16SRFFT, out10_R16SRFFT, 0.707106781186547460, MPFR_RNDN);
      mpfr_sub(out14_R16SRFFT, out14_R16SRFFT, out10_R16SRFFT, MPFR_RNDN);
  
    mpfr_add(temp_var_6, out14_R16SRFFT, out10_R16SRFFT, MPFR_RNDN);
    mpfr_add(out10_R16SRFFT, (temp_var_6), out10_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_7, out15_R16SRFFT, out11_R16SRFFT, MPFR_RNDN);
    mpfr_mul_d(temp_R16SRFFT, (temp_var_7), 0.923879532511286740, MPFR_RNDN);
  
    mpfr_mul_d(temp_var_8, out11_R16SRFFT, 1.3065629648763766, MPFR_RNDN);
    mpfr_add(out11_R16SRFFT, (temp_var_8), temp_R16SRFFT, MPFR_RNDN);
  
    mpfr_mul_d(temp_var_9, out15_R16SRFFT, (-0.54119610014619690), MPFR_RNDN);
    mpfr_add(out15_R16SRFFT, (temp_var_9), temp_R16SRFFT, MPFR_RNDN);
    mpfr_add(out8_R16SRFFT, out8_R16SRFFT, out10_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_10, out8_R16SRFFT, out10_R16SRFFT, MPFR_RNDN);
    mpfr_sub(out10_R16SRFFT, (temp_var_10), out10_R16SRFFT, MPFR_RNDN);
    mpfr_add(out12_R16SRFFT, out12_R16SRFFT, out14_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_11, out12_R16SRFFT, out14_R16SRFFT, MPFR_RNDN);
    mpfr_sub(out14_R16SRFFT, (temp_var_11), out14_R16SRFFT, MPFR_RNDN);
    mpfr_add(out9_R16SRFFT, out9_R16SRFFT, out11_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_12, out9_R16SRFFT, out11_R16SRFFT, MPFR_RNDN);
    mpfr_sub(out11_R16SRFFT, (temp_var_12), out11_R16SRFFT, MPFR_RNDN);
    mpfr_add(out13_R16SRFFT, out13_R16SRFFT, out15_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_13, out13_R16SRFFT, out15_R16SRFFT, MPFR_RNDN);
    mpfr_sub(out15_R16SRFFT, (temp_var_13), out15_R16SRFFT, MPFR_RNDN);
      mpfr_add(output_track_R16SRFFT, out8_R16SRFFT, out9_R16SRFFT, MPFR_RNDN);
  
output[1] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_sub(output_track_R16SRFFT, out8_R16SRFFT, out9_R16SRFFT, MPFR_RNDN);
  
output[7] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_add(output_track_R16SRFFT, out12_R16SRFFT, out13_R16SRFFT, MPFR_RNDN);
  
output[9] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_sub(output_track_R16SRFFT, out13_R16SRFFT, out12_R16SRFFT, MPFR_RNDN);
  
output[15] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_add(output_track_R16SRFFT, out10_R16SRFFT, out15_R16SRFFT, MPFR_RNDN);
  
output[5] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_sub(output_track_R16SRFFT, out14_R16SRFFT, out11_R16SRFFT, MPFR_RNDN);
  
output[13] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_sub(output_track_R16SRFFT, out10_R16SRFFT, out15_R16SRFFT, MPFR_RNDN);
  
output[3] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
  
    mpfr_d_sub(temp_var_14, 0.0, out14_R16SRFFT, MPFR_RNDN);
    mpfr_sub(output_track_R16SRFFT, (temp_var_14), out11_R16SRFFT, MPFR_RNDN);
  
output[11] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_add(out0_R16SRFFT, out0_R16SRFFT, out4_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_15, out0_R16SRFFT, out4_R16SRFFT, MPFR_RNDN);
    mpfr_sub(out4_R16SRFFT, (temp_var_15), out4_R16SRFFT, MPFR_RNDN);
      mpfr_add(out1_R16SRFFT, out1_R16SRFFT, out5_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_16, out1_R16SRFFT, out5_R16SRFFT, MPFR_RNDN);
    mpfr_sub(out5_R16SRFFT, (temp_var_16), out5_R16SRFFT, MPFR_RNDN);
    mpfr_add(out2_R16SRFFT, out2_R16SRFFT, out6_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_17, out2_R16SRFFT, out6_R16SRFFT, MPFR_RNDN);
    mpfr_sub(out6_R16SRFFT, (temp_var_17), out6_R16SRFFT, MPFR_RNDN);
    mpfr_add(out3_R16SRFFT, out3_R16SRFFT, out7_R16SRFFT, MPFR_RNDN);
  
    mpfr_sub(temp_var_18, out3_R16SRFFT, out7_R16SRFFT, MPFR_RNDN);
    mpfr_sub(out7_R16SRFFT, (temp_var_18), out7_R16SRFFT, MPFR_RNDN);
      mpfr_add(output_track_R16SRFFT, out0_R16SRFFT, out2_R16SRFFT, MPFR_RNDN);
  
output[0] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_sub(output_track_R16SRFFT, out0_R16SRFFT, out2_R16SRFFT, MPFR_RNDN);
  
output[4] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
    mpfr_add(out1_R16SRFFT, out1_R16SRFFT, out3_R16SRFFT, MPFR_RNDN);
  
    mpfr_add(temp_var_19, out3_R16SRFFT, out3_R16SRFFT, MPFR_RNDN);
    mpfr_sub(output_track_R16SRFFT, (temp_var_19), out1_R16SRFFT, MPFR_RNDN);
  
output[12] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(output_track_R16SRFFT, output[0], MPFR_RNDN);
      mpfr_add(output_track_R16SRFFT, output_track_R16SRFFT, out1_R16SRFFT, MPFR_RNDN);
  
output[0] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
  mpfr_set_d(output_track_R16SRFFT, output[0], MPFR_RNDN);
  
    mpfr_sub(temp_var_20, output_track_R16SRFFT, out1_R16SRFFT, MPFR_RNDN);
    mpfr_sub(output_track_R16SRFFT, (temp_var_20), out1_R16SRFFT, MPFR_RNDN);
  
output[8] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
    mpfr_set_d(temp_var_21, 0.707106781186547460, MPFR_RNDN);
    mpfr_mul_d(out5_R16SRFFT, out5_R16SRFFT, 0.707106781186547460, MPFR_RNDN);
    mpfr_set_d(temp_var_22, 0.707106781186547460, MPFR_RNDN);
    mpfr_mul_d(out7_R16SRFFT, out7_R16SRFFT, 0.707106781186547460, MPFR_RNDN);
      mpfr_sub(out5_R16SRFFT, out5_R16SRFFT, out7_R16SRFFT, MPFR_RNDN);
  
    mpfr_add(temp_var_23, out5_R16SRFFT, out7_R16SRFFT, MPFR_RNDN);
    mpfr_add(out7_R16SRFFT, (temp_var_23), out7_R16SRFFT, MPFR_RNDN);
      mpfr_sub(output_track_R16SRFFT, out6_R16SRFFT, out7_R16SRFFT, MPFR_RNDN);
  
output[14] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_add(output_track_R16SRFFT, out5_R16SRFFT, out4_R16SRFFT, MPFR_RNDN);
  
output[2] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
      mpfr_sub(output_track_R16SRFFT, out4_R16SRFFT, out5_R16SRFFT, MPFR_RNDN);
  
output[6] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
  
    mpfr_d_sub(temp_var_24, 0.0, out7_R16SRFFT, MPFR_RNDN);
    mpfr_sub(output_track_R16SRFFT, (temp_var_24), out6_R16SRFFT, MPFR_RNDN);
  
output[10] = mpfr_get_d(output_track_R16SRFFT, MPFR_RNDN);
}

void main(int argc, char *argv[])
{
 init_readconfig();
  float data[16];
  float output[16];
  mpfr_set_d(zero_main, 0, MPFR_RNDN);
  if (argc < 2)
  {
    srand(1);
  }
  else
  {
    srand(atoi(argv[1]));
  }

  int i;
  for (i = 0; i < 16; i++){
  {
    mpfr_set_d(data_track_main, (float)(rand() - RAND_MAX/2)/(RAND_MAX/2), MPFR_RNDN);
    
data[i] = mpfr_get_d(data_track_main, MPFR_RNDN);
  }

    }

  R16SRFFT(data, output);
  for (i = 0; i < 16; i++){
  {
    mpfr_set_d(output_track_main, output[i], MPFR_RNDN);
    printf("%.10lf,", mpfr_get_d(output_track_main, MPFR_RNDN));
  }

    }

}

//end of conversion, hopefully it will work :)
