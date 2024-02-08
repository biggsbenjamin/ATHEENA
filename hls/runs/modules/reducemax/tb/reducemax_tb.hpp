#ifndef REDUCEMAX_TB_HPP_
#define REDUCEMAX_TB_HPP_

#include "common.hpp"
#include "reducemax_param.hpp"

typedef ap_fixed<REDUCEMAX_DATA_WIDTH,REDUCEMAX_DATA_INT_WIDTH,AP_RND,AP_SAT> reducemax_t;

void reducemax_top(
    hls::stream<float> &in,
    hls::stream<float> &out
    //stream_t(reducemax_t) &in,
    //stream_t(reducemax_t) &out
);

#endif
