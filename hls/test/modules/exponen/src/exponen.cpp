#include "exponen_tb.hpp"
#include "exponen.hpp"

void exponen_top(
	stream_t(exp_t) &in,
	stream_t(exp_f_t) &out
)
{

#pragma HLS DATAFLOW

    // DUT
    exponen<
        EXPONEN_BATCH_SIZE,
        EXPONEN_ROWS,
        EXPONEN_COLS,
        EXPONEN_CHANNELS,
        exp_t, 
        exp_f_t
    >(in,out);

}
