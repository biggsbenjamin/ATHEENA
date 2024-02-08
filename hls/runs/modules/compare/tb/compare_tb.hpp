#ifndef COMPARE_TB_HPP_
#define COMPARE_TB_HPP_

#include "common.hpp"
#include "compare_param.hpp"

typedef ap_fixed<COMPARE_DATA_WIDTH,COMPARE_DATA_INT_WIDTH,AP_RND,AP_SAT> compare_t;

void compare_top(
    hls::stream<float> &max_in,
    hls::stream<float> &thr_in,
    float thr_val[1],
    stream_t(compare_t) &ctrl_out
);

#endif
