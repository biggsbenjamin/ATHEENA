#ifndef BUFFER_TB_HPP_
#define BUFFER_TB_HPP_

#include "common.hpp"
#include "buffer_param.hpp"

typedef ap_fixed<BUFFER_DATA_WIDTH,BUFFER_DATA_INT_WIDTH,AP_RND,AP_SAT> buffer_t;

void buffer_top(
    stream_t(buffer_t) &in,
    stream_t(buffer_t) &ctrl_in,
    stream_t(buffer_t) &out
);

#endif
