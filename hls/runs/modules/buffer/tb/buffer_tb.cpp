#include "common_tb.hpp"
#include "buffer_tb.hpp"

int main() {
    // variable initialisation
    stream_t(buffer_t) in;
    stream_t(buffer_t) ctrl_in;
    stream_t(buffer_t) out;

    // dimensions
    const int size_in  = BUFFER_BATCH_SIZE*BUFFER_ROWS*BUFFER_COLS*BUFFER_CHANNELS;
    //const int size_out = BUFFER_BATCH_SIZE*BUFFER_ROWS*BUFFER_COLS*BUFFER_FILTERS;
    //const unsigned int shape_size = BUFFER_ROWS*BUFFER_COLS*BUFFER_CHANNELS;

    // gen input
    gen_stream<buffer_t,size_in>(in);
    gen_stream<buffer_t,BUFFER_BATCH_SIZE>(ctrl_in);

    // run component
    buffer_top(in,ctrl_in,out);

}
