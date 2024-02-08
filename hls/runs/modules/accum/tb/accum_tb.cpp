#include "common_tb.hpp"
#include "accum_tb.hpp"

int main() {
    // variable initialisation
    stream_t(accum_t) in;
    stream_t(accum_t) out;

    // dimensions
    const int size_in  = ACCUM_BATCH_SIZE*ACCUM_ROWS*ACCUM_COLS*ACCUM_CHANNELS*DIVIDE(ACCUM_FILTERS,ACCUM_GROUPS);
    const int size_out = ACCUM_BATCH_SIZE*ACCUM_ROWS*ACCUM_COLS*ACCUM_FILTERS;

    // gen input
    gen_stream<accum_t,size_in>(in);

    // run component
    accum_top(in,out);

}
