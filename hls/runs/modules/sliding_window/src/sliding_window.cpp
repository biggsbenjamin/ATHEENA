#include "sliding_window_tb.hpp"
#include "sliding_window.hpp"

void sliding_window_top(
    stream_t(sliding_window_t) &in,
    stream_t(sliding_window_t) out[SLIDING_WINDOW_KERNEL_SIZE_X][SLIDING_WINDOW_KERNEL_SIZE_Y]
)
{

    #pragma HLS DATAFLOW

    sliding_window<
        SLIDING_WINDOW_BATCH_SIZE,
        SLIDING_WINDOW_ROWS,
        SLIDING_WINDOW_COLS,
        SLIDING_WINDOW_CHANNELS,
        SLIDING_WINDOW_PAD_TOP,
        SLIDING_WINDOW_PAD_RIGHT,
        SLIDING_WINDOW_PAD_BOTTOM,
        SLIDING_WINDOW_PAD_LEFT,
        SLIDING_WINDOW_STRIDE_X,
        SLIDING_WINDOW_STRIDE_Y,
        SLIDING_WINDOW_KERNEL_SIZE_X,
        SLIDING_WINDOW_KERNEL_SIZE_Y,
        sliding_window_t
    >(in,out);

}
