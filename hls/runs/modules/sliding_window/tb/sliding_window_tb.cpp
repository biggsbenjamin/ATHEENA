#include "common_tb.hpp"
#include "sliding_window_tb.hpp"

int main() {
    // variable initialisation
    stream_t(sliding_window_t) in;
    stream_t(sliding_window_t) out[SLIDING_WINDOW_KERNEL_SIZE_X][SLIDING_WINDOW_KERNEL_SIZE_Y];

    // dimensions
    const int size_in  = SLIDING_WINDOW_BATCH_SIZE*SLIDING_WINDOW_ROWS*SLIDING_WINDOW_COLS*SLIDING_WINDOW_CHANNELS;
    const int size_out = SLIDING_WINDOW_BATCH_SIZE*SLIDING_WINDOW_ROWS*SLIDING_WINDOW_COLS*SLIDING_WINDOW_CHANNELS;

    // gen input
    gen_stream<sliding_window_t,size_in>(in);

    // run component
    sliding_window_top(in,out);

}
