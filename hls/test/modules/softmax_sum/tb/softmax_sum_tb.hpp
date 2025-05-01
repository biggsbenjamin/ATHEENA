#ifndef SOFTMAX_SUM_TB_HPP_
#define SOFTMAX_SUM_TB_HPP_

#include "common.hpp"

#include "softmax_sum_param.hpp"

typedef b_float_t sfmsm_t;

/////////////////////////////////

void softmax_sum_top(
	stream_t(sfmsm_t) &in,
	stream_t(sfmsm_t) &out
    //hls::stream<float> &in,
    //hls::stream<float> &out
);

/////////////////////////////////

#endif
