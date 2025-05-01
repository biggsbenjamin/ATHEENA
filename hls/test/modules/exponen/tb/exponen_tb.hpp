#ifndef EXPONEN_TB_HPP_
#define EXPONEN_TB_HPP_

#include "common.hpp"

#include "exponen_param.hpp"

typedef b_data_t exp_t;
typedef b_float_t exp_f_t;

/////////////////////////////////

void exponen_top(
	stream_t(exp_t) &in,
	stream_t(exp_f_t) &out
);

/////////////////////////////////

#endif
