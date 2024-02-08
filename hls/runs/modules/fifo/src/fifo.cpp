#include "fifo_tb.hpp"
#include "fifo.hpp"

void fifo_top(
    stream_t(data_t) in[FIFO_COARSE],
    stream_t(data_t) out[FIFO_COARSE]
)
{

    #pragma HLS DATAFLOW

    // DUT
    fifo<
        FIFO_COARSE,  
        FIFO_DEPTH
    >(in,out);

}

