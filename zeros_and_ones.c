#include <stdio.h>

int main() {

    int input_array[] = {5,3,4,2,6,8};
    int last_index = (sizeof(input_array) / sizeof(int)) - 1;
    int output_array[last_index + 1];
    int right_products_array[last_index + 2];
    right_products_array[last_index + 1] = 1;
    int i;
    int products = 1;
    for(i = last_index; i > 0; i--) {
        products = products * input_array[i];
        right_products_array[i] = products;
        printf("%d\t%d %d\n", products, i, input_array[i]);
    }
    output_array[0] = right_products_array[1];
    products = 1;
    for(i = 1; i <= last_index; i++) {
        products = products * input_array[i - 1];
        output_array[i] = products * right_products_array[i + 1];
        printf("%d\t%d %d\n", products, i, input_array[i - 1]);
    }
    output_array[last_index] = products;
    for(i = 0; i <= last_index; i++) {
        printf("%d\t", output_array[i]);
 
return 0;
}
