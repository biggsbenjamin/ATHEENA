#include "fork_tb.hpp"
#include "fork.hpp"


void fork_top(
#if FORK_KERNEL_SIZE_X == 1 && FORK_KERNEL_SIZE_Y == 1
    stream_t(fork_t) &in,
    stream_t(fork_t) out[FORK_COARSE]
#else
    stream_t(fork_t) in[FORK_KERNEL_SIZE_X][FORK_KERNEL_SIZE_Y],
    stream_t(fork_t) out[FORK_COARSE][FORK_KERNEL_SIZE_X][FORK_KERNEL_SIZE_Y]
#endif
)
{

    #pragma HLS DATAFLOW
#if FORK_KERNEL_SIZE_X == 1 && FORK_KERNEL_SIZE_Y == 1
    fork<
        FORK_BATCH_SIZE,
        FORK_ROWS,
        FORK_COLS,
        FORK_CHANNELS,
        FORK_COARSE,
        fork_t
    >(in,out);
#else
    fork<
        FORK_BATCH_SIZE,
        FORK_ROWS,
        FORK_COLS,
        FORK_CHANNELS,
        FORK_COARSE,
        FORK_KERNEL_SIZE_X,
        FORK_KERNEL_SIZE_Y,
        fork_t
    >(in,out);
#endif

}
