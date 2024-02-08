#ifndef MEM_READ_TB_HPP_
#define MEM_READ_TB_HPP_

#include "common.hpp"
#include "mem_read_param.hpp"

void mem_read_top(
    volatile mem_int *in_hw_0,
    volatile mem_int *in_hw_1,
    volatile mem_int *in_hw_2,
    volatile mem_int *in_hw_3,
    hls::stream<data_t> in[MEM_READ_COARSE_IN]
);

#endif
