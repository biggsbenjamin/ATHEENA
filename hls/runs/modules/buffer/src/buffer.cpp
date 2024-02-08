#include "buffer_tb.hpp"
#include "buffer.hpp"


void buffer_top(
    stream_t(buffer_t) &in,
    stream_t(buffer_t) &ctrl_drop,
    stream_t(buffer_t) &out
)
{

    #pragma HLS DATAFLOW

    // DUT
    buffer<
        BUFFER_BATCH_SIZE,
        BUFFER_ROWS,
        BUFFER_COLS,
        BUFFER_CHANNELS,
        BUFFER_DROP_MODE,
        buffer_t
    >(in,ctrl_drop,out);

}

