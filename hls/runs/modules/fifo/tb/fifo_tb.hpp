#ifndef ACCUM_TB_HPP_
#define ACCUM_TB_HPP_

#include "common.hpp"
#include "fifo_param.hpp"

void accum_top(
    stream_t(data_t) in[FIFO_COARSE],
    stream_t(data_t) out[FIFO_COARSE]
);

#endif
