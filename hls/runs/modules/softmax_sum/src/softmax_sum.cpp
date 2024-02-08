#include "softmax_sum_tb.hpp"
#include "softmax_sum.hpp"


void softmax_sum_top(
    //stream_t(softmax_sum_t) &in,
    hls::stream<float> &in,
    hls::stream<float> &out
    //stream_t(softmax_sum_t) &out
)
{

    #pragma HLS DATAFLOW

    // DUT
    softmax_sum<
        SOFTMAX_SUM_BATCH_SIZE,
        SOFTMAX_SUM_ROWS,
        SOFTMAX_SUM_COLS,
        SOFTMAX_SUM_CHANNELS
    >(in,out);

}

