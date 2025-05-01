#ifndef SOFTMAX_CMP_LAYER_TB_HPP_
#define SOFTMAX_CMP_LAYER_TB_HPP_

#include "common.hpp"
#include "softmax_cmp_layer.hpp"
#include "softmax_cmp_layer_param.hpp"

void softmax_cmp_layer_top(
  stream_t(softmax_cmp_layer_data_t) in[1],
  stream_t(softmax_cmp_layer_ctrl_t) out[SOFTMAX_CMP_LAYER_CTRL]
);

#endif
