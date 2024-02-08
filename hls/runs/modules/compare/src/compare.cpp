#include "compare_tb.hpp"
#include "compare.hpp"


void compare_top(
    hls::stream<float> &max_in,
    hls::stream<float> &thr_in,
    float thr_val[1],
    stream_t(compare_t) &ctrl_out
)
{

    #pragma HLS DATAFLOW

    // DUT
    compare<
        COMPARE_BATCH_SIZE,
        compare_t
    >(max_in,thr_in,thr_val,ctrl_out);

}

