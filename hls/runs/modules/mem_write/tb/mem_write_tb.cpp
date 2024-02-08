#include "common_tb.hpp"
#include "mem_write_tb.hpp"

int main() {
    // variable initialisation
    volatile mem_int *in_hw_0;
    volatile mem_int *in_hw_1;
    volatile mem_int *in_hw_2;
    volatile mem_int *in_hw_3;
    hls::stream<data_t> in[MEM_WRITE_COARSE_OUT];
    
    // run module
    mem_write_top(
        in_hw_0,
        in_hw_1,
        in_hw_2,
        in_hw_3,
        in
    );
}
