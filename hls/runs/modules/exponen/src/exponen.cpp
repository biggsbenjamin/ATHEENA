#include "exponen_tb.hpp"
#include "exponen.hpp"


void exponen_top(
    stream_t(exponen_t) &in,
    hls::stream<float> &out
    //stream_t(exponen_t) &out
)
{

    #pragma HLS DATAFLOW

    // DUT
    exponen<
        EXPONEN_BATCH_SIZE,
        EXPONEN_ROWS,
        EXPONEN_COLS,
        EXPONEN_CHANNELS,
        exponen_t
    >(in,out);

}

