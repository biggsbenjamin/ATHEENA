#ifndef FORK_TB_HPP_
#define FORK_TB_HPP_

#include "common.hpp"
#include "fork_param.hpp"

typedef ap_fixed<FORK_DATA_WIDTH,FORK_DATA_INT_WIDTH,AP_RND,AP_SAT> fork_t;

void fork_top(
#if FORK_KERNEL_SIZE == 1
    stream_t(fork_t) &in,
    stream_t(fork_t) out[FORK_COARSE]
#else
    stream_t(fork_t) in[FORK_KERNEL_SIZE_X][FORK_KERNEL_SIZE_Y],
    stream_t(fork_t) out[FORK_COARSE][FORK_KERNEL_SIZE_X][FORK_KERNEL_SIZE_Y]
#endif
);

#endif
