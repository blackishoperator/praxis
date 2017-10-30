#include <stdio.h>

#define A_SIZE sizeof(A) / sizeof(int)

int main() {
    int A[] = {1,2,3,4,6,7,9};
    int T[30] = {};
    int i = 1;
    int j = 0;
    int k = 0;
    int l = 0;
    //checking possible choices of triples
    for(i = 1; i < A_SIZE - 1; i++) {
        for(j = 0; j < i; j++) {
            for(k = i + 1; k < A_SIZE; k++) {
                if(A[i] - A[j] < A[k] - A[i]) break;
                if(A[i] - A[j] == A[k] - A[i]) {
                    T[l++] = A[j];
                    T[l++] = A[i];
                    T[l++] = A[k];
                }
            }
        }
    }
    //print output array T
    for(i = 0; i < l; i++) {
        if(i % 3 == 0)
            printf("(");
        printf("%d", T[i]);
        if(i % 3 != 2)
            printf(" ");
        else
            printf(")\n");
        
    }

    return 0;
}
