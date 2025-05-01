#include "squeeze_tb.hpp"
#include "squeeze.hpp"


void squeeze_top(
    stream_t(squeeze_t) in[SQUEEZE_COARSE_IN],
    stream_t(squeeze_t) out[SQUEEZE_COARSE_OUT],
    int mode
)
{

#pragma HLS INLINE OFF

#pragma HLS STREAM variable=in depth=2
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in  complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0

#pragma HLS DATAFLOW


#if ( SQUEEZE_BATCH_SIZE*SQUEEZE_COLS*SQUEEZE_ROWS > 1 )
    squeeze_spatial<
        SQUEEZE_BATCH_SIZE,
        SQUEEZE_ROWS,
        SQUEEZE_COLS,
#else
    squeeze<
#endif
        SQUEEZE_CHANNELS,
        SQUEEZE_COARSE_IN,
        SQUEEZE_COARSE_OUT,
#if SQUEEZE_CHANNELS_PER_COARSE_IN > 1
        SQUEEZE_CHANNELS_PER_COARSE_IN,
        SQUEEZE_CHANNELS_PER_COARSE_IN,
#endif
#if SQUEEZE_CHANNELS_PER_COARSE_OUT > 1
        SQUEEZE_CHANNELS_PER_COARSE_OUT,
#endif
        squeeze_t
    >(in,out);

}
