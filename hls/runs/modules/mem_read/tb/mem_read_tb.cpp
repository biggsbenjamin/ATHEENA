#include "common_tb.hpp"
#include "mem_read_tb.hpp"

int main() {
    // variable initialisation
    volatile mem_int *in_hw_0;
    volatile mem_int *in_hw_1;
    volatile mem_int *in_hw_2;
    volatile mem_int *in_hw_3;
    hls::stream<data_t> in[MEM_READ_COARSE_IN];
    
    // run module
    mem_read_top(
        in_hw_0,
        in_hw_1,
        in_hw_2,
        in_hw_3,
        in
    );
}
