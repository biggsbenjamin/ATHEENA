#include "common_tb.hpp"
#include "softmax_sum_tb.hpp"

int main() {
    // variable initialisation
    //stream_t(softmax_sum_t) in;
    hls::stream<float> &in;
    hls::stream<float> &out;

    // dimensions
    const int size_in  = SOFTMAX_SUM_BATCH_SIZE*SOFTMAX_SUM_ROWS*SOFTMAX_SUM_COLS*SOFTMAX_SUM_CHANNELS;

    // gen input
    gen_stream<softmax_sum_t,size_in>(in);

    // run component
    softmax_sum_top(in,out);

}
