#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define INPUT_LEN 1000
float ydly=0.;
float iir()
{
        int i;
        float X_in,yout,coeff;
        coeff=0.9;

        X_in = ((float)(rand()-RAND_MAX/2)/(float)(RAND_MAX/2));

//        printf("\t X_in=%f ",X_in);
        yout = coeff * ydly + X_in;
        ydly = yout;
        return yout;

}

int main(int argc, char **argv)
{

  	if (argc < 2)
	{
			srand(0);
	}
	else
	{
		srand(atoi(argv[1]));
	}

        int i;
        float out;

        //~ srand(1);

        for (i=1;i<INPUT_LEN; i++)
        {

         out=iir();
         printf("%f,",out);

        }

        return 0;
}
