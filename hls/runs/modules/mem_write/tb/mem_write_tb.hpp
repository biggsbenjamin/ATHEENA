#ifndef MEM_WRITE_TB_HPP_
#define MEM_WRITE_TB_HPP_

#include "common.hpp"
#include "mem_write_param.hpp"

void mem_write_top(
    volatile mem_int *in_hw_0,
    volatile mem_int *in_hw_1,
    volatile mem_int *in_hw_2,
    volatile mem_int *in_hw_3,
    hls::stream<data_t> in[MEM_WRITE_COARSE_OUT]
);

#endif
