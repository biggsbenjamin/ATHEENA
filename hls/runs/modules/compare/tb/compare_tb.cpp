#include "common_tb.hpp"
#include "compare_tb.hpp"

int main() {
    // variable initialisation
    hls::stream<float> &max_in;
    hls::stream<float> &thr_in;
    float thr_val[1];
    thr_val[0] = 0.9;
    stream_t(compare_t) &ctrl_in;

    // dimensions
    const int size_in  = COMPARE_BATCH_SIZE;

    // gen input
    gen_stream<float,size_in>(max_in);
    gen_stream<float,size_in>(thr_in);

    // run component
    compare_top(max_in,thr_in,thr_val,ctrl_out);

}
