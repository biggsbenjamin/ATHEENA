#ifndef SPLIT_HPP_
#define SPLIT_HPP_

#include "common.hpp"

/**
 *  SPLIT FUNCTION
 */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int COARSE,
    unsigned int PORTS_OUT,
    typename split_t
>
void split(
    stream_t(split_t) in[COARSE],
    stream_t(split_t) out[PORTS_OUT][COARSE]
)
{

#pragma HLS INLINE OFF 

    const unsigned int batch_size   = BATCH_SIZE;
    const unsigned int rows         = ROWS;
    const unsigned int cols         = COLS;
    const unsigned int channels     = CHANNELS; //channels PER COARSE
    const unsigned int coarse       = COARSE;
    const unsigned int ports_out    = PORTS_OUT;

#pragma HLS STREAM variable=in 
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=out complete dim=0

    split_t local_cache[COARSE];
#pragma HLS DEPENDENCE variable=local_cache RAW intra true

    pixel_loop: for (unsigned long pixel_index = 0; pixel_index < batch_size*rows*cols*channels; pixel_index++) {
        #pragma HLS PIPELINE II=1 rewind
        ports_loop: for(unsigned int ports_index=0;ports_index < ports_out; ports_index++) {
            coarse_loop: for(unsigned int coarse_index=0;coarse_index<coarse;coarse_index++){
            #pragma HLS UNROLL
                if(ports_index == 0) {
                    DO_PRAGMA(HLS occurrence cycle=batch_size*rows*cols*channels*coarse)
                    local_cache[coarse_index] = in[coarse_index].read();
                }
                out[ports_index][coarse_index].write(local_cache[coarse_index]);
            }
        }
    }
}

#endif
