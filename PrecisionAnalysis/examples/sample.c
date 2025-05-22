#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]){

    if (argc > 1) { srand (atoi(argv[1]));} else { srand (5); }
   double a, b, c, d;
   a = (double)rand() / RAND_MAX;
   b = (double)rand() / RAND_MAX;
   c = (double)rand() / RAND_MAX;
   d = (a+b)*c;

   printf("%.10f\n", d);
   return 0;
}