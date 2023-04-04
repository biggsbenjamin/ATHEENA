#ifndef GLUE_HPP_
#define GLUE_HPP_

#include "common.hpp"

/**
 *  GLUE FUNCTION
 */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int FILTERS,
    unsigned int COARSE_IN,
    unsigned int COARSE_OUT,
    unsigned int COARSE_GROUP,
    typename glue_acc_t,
    typename glue_data_t
>
void glue(
    stream_t(glue_acc_t) in[COARSE_IN*COARSE_GROUP][COARSE_OUT],
    stream_t(glue_data_t) out[COARSE_OUT*COARSE_GROUP]
)
{

#pragma HLS INLINE OFF

    const unsigned int batch_size   = BATCH_SIZE;
    const unsigned int rows         = ROWS;
    const unsigned int cols         = COLS;
    const unsigned int filters      = FILTERS;
    const unsigned int coarse_in    = COARSE_IN;
    const unsigned int coarse_out   = COARSE_OUT;
    const unsigned int coarse_group = COARSE_GROUP;
    const unsigned int filters_per_coarse   = DIVIDE(filters,coarse_out*coarse_group);
    const unsigned int px_lim = batch_size*rows*cols*filters_per_coarse;

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in  complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0

    glue_acc_t acc[coarse_out*coarse_group], prev, tmp, glue_zero;
#pragma HLS ARRAY_PARTITION variable=acc complete dim=0
    // zero constant for acc data type
    glue_zero.data=0;

    glue_data_t outcaster;

    pixel_loop: for(unsigned int pixel_index=0;pixel_index<px_lim;pixel_index++) {
//        filter_loop: for(unsigned int filter_index=0;filter_index<filters_per_coarse;filter_index++) {
            #pragma HLS loop_flatten
            #pragma HLS pipeline II=1 rewind
            #pragma HLS unroll region
            coarse_group_loop: for(unsigned int group_index=0; group_index<coarse_group; group_index++) {
                coarse_out_loop: for(unsigned int out_index=0; out_index<coarse_out; out_index++) {
                    coarse_in_loop: for(unsigned int in_index=0; in_index<coarse_in; in_index++) {
                        // update accumulation cache
                        prev.data = ( in_index == 0 ) ? 
                            glue_zero.data : 
                            acc[group_index*coarse_out+out_index].data ;
                        //tmp var required for casting - FIXME introduce methods for casting
                        tmp = in[group_index*coarse_in+in_index][out_index].read();
                        acc[group_index*coarse_out+out_index].data = prev.data + tmp.data; 
                        acc[group_index*coarse_out+out_index].batchid = tmp.batchid;
                        // write to output stream
                        if( in_index == (coarse_in-1) ) {
                            outcaster.data = acc[group_index*coarse_out+out_index].data;
                            outcaster.batchid = acc[group_index*coarse_out+out_index].batchid;
                            out[group_index*coarse_out+out_index].write( outcaster );
                        }
                    }
                }
	        }
        //}
    }
}
#endif
