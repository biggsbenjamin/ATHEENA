#ifndef SOFTMAX_SUM_TB_HPP_
#define SOFTMAX_SUM_TB_HPP_

#include "common.hpp"
#include "softmax_sum_param.hpp"

typedef ap_fixed<SOFTMAX_SUM_DATA_WIDTH,SOFTMAX_SUM_DATA_INT_WIDTH,AP_RND,AP_SAT> softmax_sum_t;

void softmax_sum_top(
    hls::stream<float> &in,
    hls::stream<float> &out
    //stream_t(softmax_sum_t) &in,
    //stream_t(softmax_sum_t) &out
);

#endif
