#include "common_tb.hpp"
#include "reducemax_tb.hpp"

int main() {
    // variable initialisation
    //stream_t(reducemax_t) in;
    hls::stream<float> &in;
    hls::stream<float> &out;

    // dimensions
    const int size_in  = REDUCEMAX_BATCH_SIZE*REDUCEMAX_ROWS*REDUCEMAX_COLS*REDUCEMAX_CHANNELS;

    // gen input
    gen_stream<float,size_in>(in);
    //gen_stream<reducemax_t,size_in>(in);

    // run component
    reducemax_top(in,out);

}
