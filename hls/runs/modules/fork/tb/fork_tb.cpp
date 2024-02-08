#include "common_tb.hpp"
#include "fork_tb.hpp"

int main() {
    // variable initialisation
#if FORK_KERNEL_SIZE == 1
    stream_t(fork_t) in;
    stream_t(fork_t) out[FORK_COARSE];
#else
    stream_t(fork_t) in[FORK_KERNEL_SIZE_X][FORK_KERNEL_SIZE_Y];
    stream_t(fork_t) out[FORK_COARSE][FORK_KERNEL_SIZE_X][FORK_KERNEL_SIZE_Y];
#endif
    // dimensions
    const int size_in  = FORK_BATCH_SIZE*FORK_ROWS*FORK_COLS*FORK_CHANNELS;
    const int size_out = FORK_BATCH_SIZE*FORK_ROWS*FORK_COLS*FORK_CHANNELS;

    // gen input

#if FORK_KERNEL_SIZE == 1
    gen_stream<fork_t,size_in>(in);
#else
    k1_loop: for(int k1=0;k1<FORK_KERNEL_SIZE_X;k1++) {
        k2_loop: for(int k2=0;k1<FORK_KERNEL_SIZE_Y;k2++) {
            gen_stream<fork_t,size_in>(in[k1][k2]);
        }
    }
#endif

    // run component
    fork_top(in,out);

}
