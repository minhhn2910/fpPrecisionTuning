#include <stdio.h>

/* support macros for forward DCT routine from IJG jpeg library */
#define FAST_FLOAT float
#define DCTSIZE 8
#define GLOBAL(type) type

#define DCT_FLOAT_SUPPORTED

void jpeg_fdct_float(FAST_FLOAT *);

/* example 8x8 block from Wallace's overview paper */
FAST_FLOAT data[8][8] = {{139,144,149,153,155,155,155,155},
			 {144,151,153,156,159,156,156,156},
			 {150,155,160,163,158,156,156,156},
			 {159,161,162,160,160,159,159,159},
			 {159,160,161,162,162,155,155,155},
			 {161,161,161,161,160,157,157,157},
			 {162,162,161,163,162,157,157,157},
			 {162,162,161,161,163,158,158,158}};

FAST_FLOAT workspace[8][8];

int main(int argc, char *argv[])
{
  int i, j;
  int runs;

	FAST_FLOAT workspace_temp, data_temp;
  for (runs=0; runs<10; runs++) {
    /* level shift */
    for (i=0; i<8; i++) {
      for (j=0; j<8; j++) {
		  data_temp = data[i][j];
		  workspace_temp = data_temp - 128.0;
		  workspace[i][j]  = workspace_temp;
	//~ workspace[i][j] = data[i][j] - 128.0;
      }
    }
    jpeg_fdct_float((FAST_FLOAT *)workspace);
  }
  
  //printfdata
    for (i=0; i<8; i++) {
      for (j=0; j<8; j++) {
			printf("%.10f,",workspace[i][j]);
	  }
	}
  
  exit(0);
}

/* following from jpeg-6b IJG distribution */

/*
 * jfdctflt.c
 *
 * Copyright (C) 1994-1996, Thomas G. Lane.
 * This file is part of the Independent JPEG Group's software.
 * For conditions of distribution and use, see the accompanying README file.
 *
 * This file contains a floating-point implementation of the
 * forward DCT (Discrete Cosine Transform).
 *
 * This implementation should be more accurate than either of the integer
 * DCT implementations.  However, it may not give the same results on all
 * machines because of differences in roundoff behavior.  Speed will depend
 * on the hardware's floating point capacity.
 *
 * A 2-D DCT can be done by 1-D DCT on each row followed by 1-D DCT
 * on each column.  Direct algorithms are also available, but they are
 * much more complex and seem not to be any faster when reduced to code.
 *
 * This implementation is based on Arai, Agui, and Nakajima's algorithm for
 * scaled DCT.  Their original paper (Trans. IEICE E-71(11):1095) is in
 * Japanese, but the algorithm is described in the Pennebaker & Mitchell
 * JPEG textbook (see REFERENCES section in file README).  The following code
 * is based directly on figure 4-8 in P&M.
 * While an 8-point DCT cannot be done in less than 11 multiplies, it is
 * possible to arrange the computation so that many of the multiplies are
 * simple scalings of the final outputs.  These multiplies can then be
 * folded into the multiplications or divisions by the JPEG quantization
 * table entries.  The AA&N method leaves only 5 multiplies and 29 adds
 * to be done in the DCT itself.
 * The primary disadvantage of this method is that with a fixed-point
 * implementation, accuracy is lost due to imprecise representation of the
 * scaled quantization values.  However, that problem does not arise if
 * we use floating point arithmetic.
 */

/*
 * Perform the forward DCT on one block of samples.
 */

GLOBAL(void)
jpeg_fdct_float (FAST_FLOAT * data)
{
  FAST_FLOAT tmp0, tmp1, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7;
  FAST_FLOAT tmp10, tmp11, tmp12, tmp13;
  FAST_FLOAT z1, z2, z3, z4, z5, z11, z13;
  FAST_FLOAT *dataptr;
  
  FAST_FLOAT data_temp;

  int ctr;

  /* Pass 1: process rows. */

  dataptr = data;
  for (ctr = DCTSIZE-1; ctr >= 0; ctr--) {
	data_temp = dataptr[0];
	tmp0 = data_temp;
	data_temp = dataptr[7];
	tmp0 = tmp0 + data_temp;
    //~ tmp0 = dataptr[0] + dataptr[7];
    
    data_temp = dataptr[0];
	tmp7 = data_temp;
	data_temp = dataptr[7];
	tmp7 = tmp7 - data_temp;    
    //~ tmp7 = dataptr[0] - dataptr[7];

    data_temp = dataptr[1];
	tmp1 = data_temp;
	data_temp = dataptr[6];
	tmp1 = tmp1 + data_temp;  
    //~ tmp1 = dataptr[1] + dataptr[6];
    
    data_temp = dataptr[1];
	tmp6 = data_temp;
	data_temp = dataptr[6];
	tmp6 = tmp6 - data_temp;    
    //~ tmp6 = dataptr[1] - dataptr[6];
    
    data_temp = dataptr[2];
	tmp2 = data_temp;
	data_temp = dataptr[5];
	tmp2 = tmp2 + data_temp;        
    //~ tmp2 = dataptr[2] + dataptr[5];
    
    
    data_temp = dataptr[2];
	tmp5 = data_temp;
	data_temp = dataptr[5];
	tmp5 = tmp5 - data_temp;       
    //~ tmp5 = dataptr[2] - dataptr[5];

    data_temp = dataptr[3];
	tmp3 = data_temp;
	data_temp = dataptr[4];
	tmp3 = tmp3 + data_temp;    
    //~ tmp3 = dataptr[3] + dataptr[4];
    
    data_temp = dataptr[3];
	tmp4 = data_temp;
	data_temp = dataptr[4];
	tmp4 = tmp4 - data_temp;    
    //~ tmp4 = dataptr[3] - dataptr[4];
    
    /* Even part */
    
    tmp10 = tmp0 + tmp3;	/* phase 2 */
    tmp13 = tmp0 - tmp3;
    tmp11 = tmp1 + tmp2;
    tmp12 = tmp1 - tmp2;
    
    data_temp = tmp10 + tmp11; 
    dataptr[0] = data_temp;
    //~ dataptr[0] = tmp10 + tmp11; /* phase 3 */
    
    data_temp = tmp10 - tmp11;
    dataptr[4] = data_temp;
    //~ dataptr[4] = tmp10 - tmp11;
    
    z1 = (tmp12 + tmp13) * ((FAST_FLOAT) 0.707106781); /* c4 */
    
    data_temp = tmp13 + z1;
    dataptr[2] = data_temp;
    //~ dataptr[2] = tmp13 + z1;	/* phase 5 */
    
    data_temp = tmp13 - z1;
    dataptr[6] = data_temp;
    //~ dataptr[6] = tmp13 - z1;
    
    /* Odd part */

    tmp10 = tmp4 + tmp5;	/* phase 2 */
    tmp11 = tmp5 + tmp6;
    tmp12 = tmp6 + tmp7;

    /* The rotator is modified from fig 4-8 to avoid extra negations. */
    z5 = (tmp10 - tmp12) * ((FAST_FLOAT) 0.382683433); /* c6 */
    z2 = ((FAST_FLOAT) 0.541196100) * tmp10 + z5; /* c2-c6 */
    z4 = ((FAST_FLOAT) 1.306562965) * tmp12 + z5; /* c2+c6 */
    z3 = tmp11 * ((FAST_FLOAT) 0.707106781); /* c4 */

    z11 = tmp7 + z3;		/* phase 5 */
    z13 = tmp7 - z3;

	data_temp = z13 + z2;
	dataptr[5] = data_temp;
    //~ dataptr[5] = z13 + z2;	/* phase 6 */
    
    data_temp = z13 - z2;
    dataptr[3] = data_temp;
    //~ dataptr[3] = z13 - z2;
    
    data_temp = z11 + z4;
    dataptr[1] = data_temp;
    //~ dataptr[1] = z11 + z4;
    
    
    data_temp = z11 - z4;
    dataptr[7]  = data_temp ;
    //~ dataptr[7] = z11 - z4;

    dataptr += DCTSIZE;		/* advance pointer to next row */
  }

  /* Pass 2: process columns. */

  dataptr = data;
  for (ctr = DCTSIZE-1; ctr >= 0; ctr--) {
	  
  /*  tmp0 = dataptr[DCTSIZE*0] + dataptr[DCTSIZE*7];
    tmp7 = dataptr[DCTSIZE*0] - dataptr[DCTSIZE*7];
    tmp1 = dataptr[DCTSIZE*1] + dataptr[DCTSIZE*6];
    tmp6 = dataptr[DCTSIZE*1] - dataptr[DCTSIZE*6];
    tmp2 = dataptr[DCTSIZE*2] + dataptr[DCTSIZE*5];
    tmp5 = dataptr[DCTSIZE*2] - dataptr[DCTSIZE*5];
    tmp3 = dataptr[DCTSIZE*3] + dataptr[DCTSIZE*4];
    tmp4 = dataptr[DCTSIZE*3] - dataptr[DCTSIZE*4];
    **/

	data_temp = dataptr[DCTSIZE*0];
	tmp0 = data_temp;
	data_temp = dataptr[DCTSIZE*7];
	tmp0 = tmp0 + data_temp;
  
    
    data_temp = dataptr[DCTSIZE*0];
	tmp7 = data_temp;
	data_temp = dataptr[DCTSIZE*7];
	tmp7 = tmp7 - data_temp;    
 

    data_temp = dataptr[DCTSIZE*1];
	tmp1 = data_temp;
	data_temp = dataptr[DCTSIZE*6];
	tmp1 = tmp1 + data_temp;  

    
    data_temp = dataptr[DCTSIZE*1];
	tmp6 = data_temp;
	data_temp = dataptr[DCTSIZE*6];
	tmp6 = tmp6 - data_temp;    

    
    data_temp = dataptr[DCTSIZE*2];
	tmp2 = data_temp;
	data_temp = dataptr[DCTSIZE*5];
	tmp2 = tmp2 + data_temp;        
 
    
    
    data_temp = dataptr[DCTSIZE*2];
	tmp5 = data_temp;
	data_temp = dataptr[DCTSIZE*5];
	tmp5 = tmp5 - data_temp;       
 

    data_temp = dataptr[DCTSIZE*3];
	tmp3 = data_temp;
	data_temp = dataptr[DCTSIZE*4];
	tmp3 = tmp3 + data_temp;    

    
    data_temp = dataptr[DCTSIZE*3];
	tmp4 = data_temp;
	data_temp = dataptr[DCTSIZE*4];
	tmp4 = tmp4 - data_temp;    


    
    
    /* Even part */
    
    tmp10 = tmp0 + tmp3;	/* phase 2 */
    tmp13 = tmp0 - tmp3;
    tmp11 = tmp1 + tmp2;
    tmp12 = tmp1 - tmp2;
    
    data_temp = tmp10 + tmp11;
    dataptr[DCTSIZE*0] = data_temp;
    //~ dataptr[DCTSIZE*0] = tmp10 + tmp11; /* phase 3 */
    
    data_temp = tmp10 - tmp11;
    dataptr[DCTSIZE*4] = data_temp;
    
    //~ dataptr[DCTSIZE*4] = tmp10 - tmp11;
    
    z1 = (tmp12 + tmp13) * ((FAST_FLOAT) 0.707106781); /* c4 */
    
    data_temp =   tmp13 + z1; 
    dataptr[DCTSIZE*2] = data_temp;
    //~ dataptr[DCTSIZE*2] = tmp13 + z1; /* phase 5 */
    
    data_temp = tmp13 - z1;
    dataptr[DCTSIZE*6] = data_temp;
    //~ dataptr[DCTSIZE*6] = tmp13 - z1;
    
    /* Odd part */

    tmp10 = tmp4 + tmp5;	/* phase 2 */
    tmp11 = tmp5 + tmp6;
    tmp12 = tmp6 + tmp7;

    /* The rotator is modified from fig 4-8 to avoid extra negations. */
    z5 = (tmp10 - tmp12) * ((FAST_FLOAT) 0.382683433); /* c6 */
    z2 = ((FAST_FLOAT) 0.541196100) * tmp10 + z5; /* c2-c6 */
    z4 = ((FAST_FLOAT) 1.306562965) * tmp12 + z5; /* c2+c6 */
    z3 = tmp11 * ((FAST_FLOAT) 0.707106781); /* c4 */

    z11 = tmp7 + z3;		/* phase 5 */
    z13 = tmp7 - z3;

	data_temp = z13 + z2;
	dataptr[DCTSIZE*5] = data_temp;
    //~ dataptr[DCTSIZE*5] = z13 + z2; /* phase 6 */
    
    data_temp = z13 - z2;
    dataptr[DCTSIZE*3] = data_temp;
    //~ dataptr[DCTSIZE*3] = z13 - z2;
    data_temp = z11 + z4;  
    dataptr[DCTSIZE*1] = data_temp;
    //~ dataptr[DCTSIZE*1] = z11 + z4;
    data_temp = z11 - z4;
    dataptr[DCTSIZE*7] = data_temp;
    //~ dataptr[DCTSIZE*7] = z11 - z4;

    dataptr++;			/* advance pointer to next column */
  }
}

