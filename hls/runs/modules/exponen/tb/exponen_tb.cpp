#include "common_tb.hpp"
#include "exponen_tb.hpp"

int main() {
    // variable initialisation
    stream_t(exponen_t) in;
    //stream_t(exponen_t) out;
    hls::stream<float> &out

    // dimensions
    const int size_in  = EXPONEN_BATCH_SIZE*EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_CHANNELS;
    //const int size_out = EXPONEN_BATCH_SIZE*EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_FILTERS;
    //const unsigned int shape_size = EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_CHANNELS;

    // gen input
    gen_stream<exponen_t,size_in>(in);
    //gen_stream<exponen_t,EXPONEN_BATCH_SIZE>(ctrl_in);

    // run component
    exponen_top(in,out);

}
