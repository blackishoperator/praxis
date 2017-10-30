#include <stdio.h>

#define A_SIZE sizeof(A) / sizeof(int)

int main() {
    int A[10] = {1,2,3,4,5,6,7,8,9,10};
    int T[99];
    int i = 1;
    int j = 0;
    int k = 0;
    int l = 0;

    for(i = 1; i < A_SIZE - 1; i++) {
        for(j = 0; j < i; j++) {
            for(k = i + 1; k < A_SIZE; k++) {
                printf("A[%d] = %d\tA[%d] = %d\tA[%d] = %d\n", j, A[j], i, A[i], k, A[k]);
                if(A[j] - A[i] < A[k] - A[i]) break;
                if(A[j] - A[i] == A[k] - A[i]) {
                    T[l++] = A[j];
                    T[l++] = A[i];
                    T[l++] = A[k];
                }
            }
        }
    }
    
    for(i = 0; i < l; i++)
        printf("%d\t", T[i]);
    printf("\n");

    return 0;
}
