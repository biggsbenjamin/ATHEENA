#ifndef CONCAT_HPP_
#define CONCAT_HPP_

#include "common.hpp"

template<
    typename MULTI_CHANNELS,
    const unsigned int BATCH_SIZE,
    const unsigned int ROWS,
    const unsigned int COLS,
    const unsigned int PORTS_IN,
    const MULTI_CHANNELS CHANNELS,
    typename concat_t
>
void concat(
    stream_t(concat_t) in[PORTS_IN],
    stream_t(concat_t) &out
    ) {

    #pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const MULTI_CHANNELS channels = CHANNELS;
    const unsigned int ports_in   = PORTS_IN;

    const unsigned int channels_out = CHANNELS;

    DO_PRAGMA(HLS STREAM variable=in depth=channels_out+1)
    #pragma HLS ARRAY_PARTITION variable=in complete dim=0
    #pragma HLS STREAM variable=out

    void channel_loop( stream_t(concat_t) in[ports_in], stream_t(concat_t) &out, int port_index ) {
        #pragma HLS inline off
        channel_loop: for(unsigned int channel_index=0; channel_index<channels; channel_index++) {
            #pragma HLS PIPELINE II=1 rewind
            out.write(in[port_index].read());
        }
    }

    dim_loop: for(unsigned long pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {

        #pragma HLS dependence variable out intra WAW true
        #pragma HLS pipeline
        #pragma HLS unroll region

        ports_loop: for(unsigned int port_index=0; port_index<ports_in; port_index++) {
            channel_loop(in,out,port_index);
        }
    }
}
