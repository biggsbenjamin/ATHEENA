#ifndef EXIT_MERGE_HPP_
#define EXIT_MERGE_HPP_

#include "common.hpp"
/* adding this between in, ctr_in and the conditional layer 
 * so there can be buffering */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename     intr_t
> void em_buff(
    stream_t(intr_t) &in, //might need a float version too
    //stream_t(b_bool_t) &ctrl_drop, 
    stream_t(intr_t) &out
)
{
    #pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;

    const unsigned int buff_size  = rows*cols*channels;
    const unsigned int invalid_id = 65535;

    intr_t cache;
    full_loop: 
    for(unsigned long b_index=0;b_index<batch_size;b_index++) {
        for(unsigned long px_index=0;px_index<buff_size;px_index++) {
            #pragma HLS PIPELINE II=1
            cache = in.read();

            if (cache.batchid != invalid_id ) {
              out.write( cache );
            } 
        }
        //printf("done bidx:%d \n", b_index);
    }
}

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int EXITS,
    typename em_t
> void merger(
    stream_t(em_t) in[EXITS], 
    stream_t(em_t) &out
)
{
#pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;
    const unsigned int exits      = EXITS;
    const unsigned int fm_size    = ROWS*COLS*CHANNELS;
    const unsigned int full_size  = BATCH_SIZE*ROWS*COLS*CHANNELS;

    const unsigned int depth_in = full_size+8;
    #pragma HLS ARRAY_PARTITION variable=in complete dim=0
    #pragma HLS STREAM variable=out

    em_t cache;
    unsigned int b_index=0;

    batch_loop: 
    //for(unsigned long b_index=0;b_index<batch_size;b_index++) {
    while (b_index < batch_size) {

        exit_loop: 
        for(unsigned int ex_idx=0;ex_idx<exits;ex_idx++){
        //#pragma HLS UNROLL
             if (!in[ex_idx].empty()){
                samp_loop: 
                for(unsigned long pxo_index=0;pxo_index<fm_size;pxo_index++) {
                #pragma HLS PIPELINE II=1 //rewind
                    cache = in[ex_idx].read();
                    out.write(cache); 
                } 
                printf("printing at end of samp loop b idx:%d done \n",b_index);
                b_index++;
            }   
        }
    }
}

//ktemplate<
//k    unsigned int BATCH_SIZE,
//k    unsigned int ROWS,
//k    unsigned int COLS,
//k    unsigned int CHANNELS,
//k    unsigned int EXITS,
//k    typename em_t
//k>
//kvoid exit_merge(
//k    stream_t(em_t) in[EXITS], 
//k    stream_t(em_t) &out
//k)
//k{
//k#pragma HLS INLINE OFF
//k
//k    const unsigned int batch_size = BATCH_SIZE;
//k    const unsigned int rows       = ROWS;
//k    const unsigned int cols       = COLS;
//k    const unsigned int channels   = CHANNELS;
//k    const unsigned int exits      = EXITS;
//k    const unsigned int fm_size    = ROWS*COLS*CHANNELS;
//k    const unsigned int full_size  = BATCH_SIZE*ROWS*COLS*CHANNELS;
//k
//k    #pragma HLS ARRAY_PARTITION variable=in complete dim=0
//k    #pragma HLS STREAM variable=out
//k
//k    stream_t(em_t) exits_intr[exits];
//k    #pragma HLS STREAM variable=exits_intr
//k    const unsigned int depth_in = full_size+1;
//k    #pragma HLS STREAM variable=exits_intr depth=depth_in
//k
//k    // forcing hls to gen fifos for internal streams
//k    for (int ex=0; ex<exits; ex++) {
//k        #pragma HLS unroll
//k        em_buff<
//k            BATCH_SIZE,
//k            ROWS,
//k            COLS,
//k            CHANNELS,
//k            em_t
//k        >(in[ex], exits_intr[ex]);
//k    }
//k
//k    merger<
//k        BATCH_SIZE,
//k        ROWS,
//k        COLS,
//k        CHANNELS,
//k        EXITS,
//k        em_t
//k    >(exits_intr, out);
//k
//k}

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int EXITS,
    typename em_t
>
void exit_merge(
    stream_t(em_t) in[EXITS], 
    stream_t(em_t) &out
)
{
#pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;
    const unsigned int exits      = EXITS;
    const unsigned int fm_size    = ROWS*COLS*CHANNELS;
    const unsigned int full_size  = BATCH_SIZE*ROWS*COLS*CHANNELS;

    const unsigned int depth_in = full_size+8;
    #pragma HLS STREAM variable=in depth=depth_in
    #pragma HLS ARRAY_PARTITION variable=in complete dim=0
    #pragma HLS STREAM variable=out

    em_t cache;
    unsigned int b_index=0;
    batch_loop: 
    //for(unsigned long b_index=0;b_index<batch_size;b_index++) {
    while (b_index < batch_size) {

        //bool exits_empty=true;
        //while (exits_empty) {
        //    for(unsigned int ex_idx=0;ex_idx<exits;ex_idx++){
        //    #pragma HLS UNROLL
        //        exits_empty &= in[ex_idx].empty();
        //    }
        //}

        exit_loop: 
        for(unsigned int ex_idx=0;ex_idx<exits;ex_idx++){
        //#pragma HLS UNROLL
             if (!in[ex_idx].empty()){
                samp_loop: 
                for(unsigned long pxo_index=0;pxo_index<fm_size;pxo_index++) {
                #pragma HLS PIPELINE II=1 //rewind
                    cache = in[ex_idx].read();
                    out.write(cache); 
                } 
                b_index++;
            }   
        }

        /*if (!in_early.empty()){
            samp_loop_early: for(unsigned long pxo_index=0;pxo_index<fm_size;pxo_index++) {
                //out.write(early_batch_id.read());
                out.write(in_early.read()); 
            }
        
        } else if (!in_late.empty()) {
            samp_loop_late: for(unsigned long pxo_index=0;pxo_index<fm_size;pxo_index++) {
                //out.write(late_batch_id.read());
                out.write(in_late.read()); 
            }
        }*/
    }
}

#endif

