#include "softmax_sum_tb.hpp"
#include "softmax_sum.hpp"

void softmax_sum_top(
    stream_t(sfmsm_t) &in,
    stream_t(sfmsm_t) &out
    //hls::stream<float> &in,
    //hls::stream<float> &out
)
{

#pragma HLS DATAFLOW

    // DUT
    softmax_sum<
        SOFTMAX_SUM_BATCH_SIZE,
        SOFTMAX_SUM_ROWS,
        SOFTMAX_SUM_COLS,
        SOFTMAX_SUM_CHANNELS,
        sfmsm_t
    >(in,out);

}
