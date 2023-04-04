#ifndef EXPONEN_HPP_
#define EXPONEN_HPP_

#include "common.hpp"

/**
 * EXPONENTIAL FUNCTION
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename exp_t,
    typename exp_f_t
>
void exponen(
    stream_t(exp_t) &in,
    stream_t(exp_f_t) &out
)
{

#pragma HLS INLINE OFF //prevents functions being inlined
    
    const unsigned int batch_size   = BATCH_SIZE;
    const unsigned int rows         = ROWS;
    const unsigned int cols         = COLS;
    const unsigned int channels     = CHANNELS;
    //might not need these constants?
    exp_t exp_max_in, data_max;
    exp_max_in.data             = 4.84375;
    data_max.data               = 127.99609375;
 
    // const unsigned int depth_in= rows*cols*channels+15; //FIXME WHY did i do this???
#pragma HLS STREAM variable=in depth=41 //25(exp pipeline dpth) + 16(buffer) //OLD -> depth_in
#pragma HLS STREAM variable=out //sets up streaming data type
    
    exp_t cache;
    exp_f_t out_var;
    for(unsigned long pixel_index=0 ; pixel_index < batch_size*rows*cols*channels ; pixel_index++) {
#pragma HLS PIPELINE II=1 rewind 
        /*exp_t tmp, res;
        tmp = exp_t{ in.read() };
        
        res = hls::exp(tmp);
        
        if (res < 0) { //sat value
            res = data_max; //approx of the same sat behaviour as data_t
        }
        out.write( data_t{res} );*/

        // read fixed point in and batch id
        cache = in.read();
        // prepare float output var
        out_var.batchid = cache.batchid;
        // make use of naff hls thing
        out_var.data = hls::exp( cache.data.to_float() );
        out.write(out_var);
    }
}

#endif

