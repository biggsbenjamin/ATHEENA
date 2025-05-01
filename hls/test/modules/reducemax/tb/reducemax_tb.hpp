#ifndef REDUCEMAX_TB_HPP_
#define REDUCEMAX_TB_HPP_

#include "common.hpp"

#include "reducemax_param.hpp"

typedef b_float_t rdmx_t;

/////////////////////////////////

void reducemax_top(
	stream_t(rdmx_t) &in,
	stream_t(rdmx_t) &out
    //hls::stream<float> &in,
    //hls::stream<float> &out
);

/////////////////////////////////

#endif
