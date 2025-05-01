#include "softmax_cmp_layer_tb.hpp"
#include "softmax_cmp_layer.hpp"

void softmax_cmp_layer_top(
  stream_t(softmax_cmp_layer_data_t) in[1], //change to coarse if needed
  stream_t(softmax_cmp_layer_ctrl_t) out[SOFTMAX_CMP_LAYER_CTRL]
)
{
#pragma HLS DATAFLOW
//#pragma HLS INTERFACE ap_ctrl_chain port=return

//#pragma HLS INTERFACE axis port=in
//#pragma HLS INTERFACE axis port=out

////#pragma HLS STREAM variable=in
////#pragma HLS STREAM variable=out

#pragma HLS INTERFACE s_axilite port=return bundle=ctrl
#pragma HLS INTERFACE axis port=in
#pragma HLS INTERFACE axis port=out

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out


    softmax_cmp_layer(in,out);

}
