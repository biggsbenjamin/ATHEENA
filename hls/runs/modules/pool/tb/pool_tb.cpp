#include "common_tb.hpp"
#include "pool_tb.hpp"

int main() {
    // variable initialisation
    stream_t(pool_t) in[POOL_KERNEL_SIZE][POOL_KERNEL_SIZE];
    stream_t(pool_t) out;

    // dimensions
    const int size_in  = POOL_BATCH_SIZE*POOL_ROWS*POOL_COLS*POOL_CHANNELS;
    const int size_out = POOL_BATCH_SIZE*POOL_ROWS*POOL_COLS*POOL_CHANNELS;

    // gen input
    k1_loop: for(int k1=0;k1<POOL_KERNEL_SIZE;k1++) {
        k2_loop: for(int k2=0;k1<POOL_KERNEL_SIZE;k2++) {
            gen_stream<pool_t,size_in>(in[k1][k2]);
        }
    }

    // run component
    pool_top(in,out);

}
