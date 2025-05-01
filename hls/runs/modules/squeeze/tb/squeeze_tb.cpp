#include "common_tb.hpp"
#include "squeeze_tb.hpp"

int main() {
    // variable initialisation
    stream_t(squeeze_t) in[SQUEEZE_COARSE_IN];
    stream_t(squeeze_t) out[SQUEEZE_COARSE_OUT];
    // dimensions
    const int size_in  = SQUEEZE_BATCH_SIZE*SQUEEZE_ROWS*SQUEEZE_COLS*SQUEEZE_CHANNELS;
    const int size_out = SQUEEZE_BATCH_SIZE*SQUEEZE_ROWS*SQUEEZE_COLS*SQUEEZE_CHANNELS;

    // gen input


    // run component
    squeeze_top(in,out);

}
