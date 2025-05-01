#include "compare_tb.hpp"
#include "compare.hpp"

void compare_top(
    //hls::stream<float> &max_in,
    //hls::stream<float> &thr_in,
    stream_t(cmp_t) &max_in,
    stream_t(cmp_t) &thr_in,
    float thr_val[1],
    stream_t(ctrl_t) &out
)
{

#pragma HLS DATAFLOW

    // DUT
    compare<
        COMPARE_BATCH_SIZE,
        cmp_t,
        ctrl_t
    >(max_in, thr_in, thr_val, out);

}
