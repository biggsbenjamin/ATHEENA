#ifndef COMPARE_TB_HPP_
#define COMPARE_TB_HPP_

#include "common.hpp"

#include "compare_param.hpp"

typedef b_float_t cmp_t;
//typedef b_data_t ctrl_t;
typedef b_bool_t ctrl_t;

/////////////////////////////////

void compare_top(
    //hls::stream<float> &max_in,
    //hls::stream<float> &thr_in,
    stream_t(cmp_t) &max_in,
    stream_t(cmp_t) &thr_in,
    float thr_val[1],
    stream_t(ctrl_t) &out
);

/////////////////////////////////

#endif
