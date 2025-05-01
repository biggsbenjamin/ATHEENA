#include "reducemax_tb.hpp"
#include "reducemax.hpp"

void reducemax_top(
    stream_t(rdmx_t) &in,
    stream_t(rdmx_t) &out
    //hls::stream<float> &in,
    //hls::stream<float> &out
)
{

#pragma HLS DATAFLOW

    // DUT
    reducemax<
        REDUCEMAX_BATCH_SIZE,
        REDUCEMAX_ROWS,
        REDUCEMAX_COLS,
        REDUCEMAX_CHANNELS,
        rdmx_t
    >(in,out);

}
