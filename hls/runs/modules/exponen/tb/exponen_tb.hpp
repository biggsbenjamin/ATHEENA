#ifndef EXPONEN_TB_HPP_
#define EXPONEN_TB_HPP_

#include "common.hpp"
#include "exponen_param.hpp"

typedef ap_fixed<EXPONEN_DATA_WIDTH,EXPONEN_DATA_INT_WIDTH,AP_RND,AP_SAT> exponen_t;

void exponen_top(
    stream_t(exponen_t) &in,
    hls::stream<float> &out
    //stream_t(exponen_t) &out
);

#endif
