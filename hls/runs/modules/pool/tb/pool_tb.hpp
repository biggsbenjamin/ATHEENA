#ifndef POOL_TB_HPP_
#define POOL_TB_HPP_

#include "common.hpp"
#include "pool_param.hpp"

typedef ap_fixed<POOL_DATA_WIDTH,POOL_DATA_INT_WIDTH,AP_RND,AP_SAT> pool_t;

void pool_top(
    stream_t(pool_t) in[POOL_KERNEL_SIZE][POOL_KERNEL_SIZE],
    stream_t(pool_t) &out
);

#endif
