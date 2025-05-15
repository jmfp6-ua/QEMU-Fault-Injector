#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

#define NUMS_SIZE 6

int32_t sumArray(int32_t* nums, int32_t size){
        int32_t total = 0;
        for(int i = 0; i < size; i++){
                total += nums[i];
        }
        return total;
}

int main()
{
        int32_t nums[NUMS_SIZE] = {5,5,5,5,5,5};
        int32_t *extra = (int32_t*)malloc(sizeof(int32_t));
        *extra = 5;
        int32_t sum = sumArray(nums, NUMS_SIZE);
        sum += *extra;
        printf("Sum of array = %d\n", sum);
        return 0;
}