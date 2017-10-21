#include <stdio.h>

int main() {

    int d[] = {1,0,1,1,1,0,1,1,1,1,0,1,1,1,1,0,0,1,1};
    int d_size = sizeof(d)/sizeof(int);
    int i = 0;
    int best_zero_index = -1;   //holds the answer
    int prev_zero_index = -1;   //holds previous zero index
    int post_zero_streak = 0;   //number of ones after a zero
    int pre_zero_streak = 0;    //number of ones before a zero
    int max_ones_streak = 0;    //holds maximum ones streak length

    for(i = 0; i <= d_size; i++) {  //from 0 to sizeof(d) + 1, last enumartion supposes the array ends with zero

        if(i == d_size || d[i] == 0) {
            if((pre_zero_streak + post_zero_streak + 1) >= max_ones_streak) {   //checks for a better answer
                best_zero_index = prev_zero_index;
                max_ones_streak = pre_zero_streak + post_zero_streak + 1;
            }

            pre_zero_streak = post_zero_streak;
            post_zero_streak = 0;
            prev_zero_index = i;
        }

        else {
            post_zero_streak += 1;
        }

    }

    printf("best zero index:%d\n", best_zero_index);
    return 0;
}
