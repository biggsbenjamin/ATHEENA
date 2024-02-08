#include "common_tb.hpp"
#include "fifo_tb.hpp"

int main() {
    // variable initialisation
    stream_t(data_t) in[FIFO_COARSE];
    stream_t(data_t) out[FIFO_COARSE];

    // dimensions
    const int size_in  = 1;
    const int size_out = 1;

    // gen input
    coarse_loop: for(int i=0;i<FIFO_COARSE;i++) {
        gen_stream<data_t,size_in>(in[i]);
    }

    // run component
    fifo_top(in,out);

}
