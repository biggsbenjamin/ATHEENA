#ifndef ACCUM_TB_HPP_
#define ACCUM_TB_HPP_

#include "common.hpp"
#include "accum_param.hpp"

typedef ap_fixed<ACCUM_DATA_WIDTH,ACCUM_DATA_INT_WIDTH,AP_RND,AP_SAT> accum_t;

void accum_top(
    stream_t(accum_t) &in,
    stream_t(accum_t) &out
);

#endif
