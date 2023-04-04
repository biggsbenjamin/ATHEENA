#ifndef BIAS_HPP_ //required to prevent multiple definition error
#define BIAS_HPP_

#include "common.hpp"

/**
 *  BIAS FUNCTION
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int FILTERS,
    typename bias_data_t,
    typename bias_biases_t
>
void bias(
    stream_t(bias_data_t) &in,
    const bias_biases_t bias[FILTERS],
    stream_t(bias_data_t) &out
)
{

#pragma HLS INLINE OFF 

    const unsigned int batch_size   = BATCH_SIZE;
    const unsigned int rows         = ROWS;
    const unsigned int cols         = COLS;
    const unsigned int filters      = FILTERS;

#pragma HLS STREAM variable=in 
#pragma HLS STREAM variable=out

    bias_data_t tmp;

    pixel_loop: for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        filter_loop: for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
            #pragma HLS PIPELINE II=1 rewind
            #pragma HLS loop_flatten
            tmp = in.read();
            tmp.data = tmp.data + bias[filter_index];
            out.write(tmp);
	    }
    }
}

#endif
