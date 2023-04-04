#ifndef BUFFER_HPP_
#define BUFFER_HPP_

#include "common.hpp"

/* adding this between in, ctr_in and the conditional layer 
 * so there can be buffering */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename     intr_t
>
void buffer_buff(
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

    intr_t cache;

    full_loop: 
    for(unsigned long b_index=0;b_index<batch_size*buff_size;b_index++) {
        #pragma HLS PIPELINE II=1
        cache = in.read();
        out.write( cache );
    }
}

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename     full_t,
    typename     intr_t
>
void buffer_buff(
    stream_t(full_t) &in, //might need a float version too
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

    //intr_t cache;
    full_t cache;

    full_loop: 
    for(unsigned long b_index=0;b_index<batch_size*buff_size;b_index++) {
        #pragma HLS PIPELINE II=1
        cache = in.read();
        out.write( cache.data );
    }
}

/* adding this between in, ctr_in and the conditional layer 
 * so there can be buffering */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename     full_t,
    typename     intr_t
>
void buffer_buff_bsplit(
    stream_t(full_t) &in, //might need a float version too
    stream_t(intr_t) out[BATCH_SIZE]
)
{
    #pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;

    const unsigned int buff_size  = rows*cols*channels;

    full_t cache;

    full_loop: 
    for(unsigned long b_index=0;b_index<batch_size;b_index++) {
        for (unsigned int px_idx=0; px_idx<buff_size; px_idx++) {
            #pragma HLS PIPELINE II=1
            cache = in.read();
            out[b_index].write( cache.data );
        }
    }
}

/* part of the buffer module that does the dropping */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    bool         DROP_MODE, //true = drop on 1, false = drop on 0
    typename     buffer_t
>
void buffer_big_conditional(
    //stream_t(buffer_t) in[BATCH_SIZE],
    stream_t(data_t) in[BATCH_SIZE], //might need a float version too
    stream_t(b_bool_t) &ctrl_drop, 
    stream_t(buffer_t) &out
)
{
    #pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;
    const bool drop_mode          = DROP_MODE;

    const unsigned int buff_size  = rows*cols*channels;

    #pragma HLS STREAM variable=in
    #pragma HLS STREAM variable=out
    #pragma HLS STREAM variable=ctrl_drop

    b_bool_t drop_tmp;
    data_t data_tmp, data_tmp2;
    //buffer_t data_tmp, data_tmp2;
    buffer_t out_var;//,flusher;
    unsigned int b_index=0;
    unsigned int px_index=0;
    bool pass_thru=true;

    unsigned int lp_ctr = 0;

    batch_loop: 
    while (b_index < batch_size) {
        #pragma HLS PIPELINE II=2


        if (px_index == 0){
            drop_tmp = ctrl_drop.read();
            pass_thru = ((drop_tmp.data == 1 && !drop_mode) || 
                    (drop_tmp.data == 0 && drop_mode));
        }

    	data_tmp = in[b_index].read();
        if (px_index+1 < buff_size) {
            // the case of odd number of pixels
    	    data_tmp2 = in[b_index].read();
        }

        if (pass_thru){
            out_var.batchid = drop_tmp.batchid;
            out_var.data = data_tmp;
            out.write(out_var);
            px_index++;

            if (px_index < buff_size) {
                //out_var.batchid = drop_tmp.batchid;
                out_var.data = data_tmp2;
                out.write(out_var);
                px_index++;
            }

            if (px_index >= buff_size) {
                px_index=0;
                b_index++;
            }

        } else {
            px_index=0;
            b_index++;
        }
    }

    // in the case that the last sample is difficult:
    // still need to perform the flush TODO
    flush_loop: 
    for(unsigned long pxi_index=0;pxi_index<20*buff_size;pxi_index++) {
        #pragma HLS PIPELINE II=1 
        //penultimate sample will either be data or flush the pipeline
        out_var.batchid = 420;
        out_var.data = 6.9;
        out.write(out_var);
    }

}

/* OLD VERSION OF more clever conditional */
//template<
//    unsigned int BATCH_SIZE,
//    unsigned int ROWS,
//    unsigned int COLS,
//    unsigned int CHANNELS,
//    bool         DROP_MODE, //true = drop on 1, false = drop on 0
//    typename     buffer_t
//>
//void buffer_conditional(
//    stream_t(buffer_t) in[BATCH_SIZE], //might need a float version too
//    stream_t(b_bool_t) &ctrl_drop, 
//    stream_t(buffer_t) &out
//)
//{
//    #pragma HLS INLINE OFF
//
//    const unsigned int batch_size = BATCH_SIZE;
//    const unsigned int rows       = ROWS;
//    const unsigned int cols       = COLS;
//    const unsigned int channels   = CHANNELS;
//    const bool drop_mode          = DROP_MODE;
//
//    const unsigned int buff_size  = rows*cols*channels;
//
//    #pragma HLS STREAM variable=in
//    #pragma HLS STREAM variable=out
//    #pragma HLS STREAM variable=ctrl_drop
//
//    b_bool_t drop_tmp;
//    buffer_t data_tmp, data_tmp2;
//    buffer_t flusher;
//    unsigned int b_index=0;
//    unsigned int px_index=0;
//    bool pass_thru=true;
//
//    unsigned int lp_ctr = 0;
//
//    batch_loop: 
//    while (b_index < batch_size) {
//        #pragma HLS PIPELINE II=2
//
//
//        if (px_index == 0){
//            drop_tmp = ctrl_drop.read();
//            pass_thru = ((drop_tmp.data == 1 && !drop_mode) || 
//                    (drop_tmp.data == 0 && drop_mode));
//        }
//
//    	data_tmp = in[b_index].read();
//        if (px_index+1 < buff_size) {
//            // the case of odd number of pixels
//    	    data_tmp2 = in[b_index].read();
//        }
//
//        if (pass_thru){
//            out.write(data_tmp);
//            px_index++;
//
//            if (px_index < buff_size) {
//                out.write(data_tmp2);
//                px_index++;
//            }
//
//            if (px_index >= buff_size) {
//                px_index=0;
//                b_index++;
//            }
//
//        } else {
//            px_index=0;
//            b_index++;
//        }
//    }
//
//    // in the case that the last sample is difficult:
//    // still need to perform the flush TODO
//    flush_loop: 
//    for(unsigned long pxi_index=0;pxi_index<2*buff_size;pxi_index++) {
//        #pragma HLS PIPELINE II=1 
//        //penultimate sample will either be data or flush the pipeline
//        flusher.batchid = 420;
//        flusher.data = 6.9;
//        out.write(flusher);
//    }
//
//}

/* slow but less resources */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    bool         DROP_MODE, //true = drop on 1, false = drop on 0
    typename     buffer_t,
    typename     intr_t
>
void buffer_conditional(
    stream_t(intr_t) &in,
    stream_t(b_bool_t) &ctrl_drop, 
    stream_t(buffer_t) &out
)
{
    #pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;
    const bool drop_mode          = DROP_MODE;

    //TODO add template value for buffer size
    const unsigned int buff_size  = rows*cols*channels;

    b_bool_t drop_tmp;
    intr_t cache;
    buffer_t out_var;

    batch_loop: 
    for(unsigned long b_index=0;b_index<batch_size;b_index++) {
        samp_loop: 
        for(unsigned long pxi_index=0;pxi_index<buff_size;pxi_index++) {
        #pragma HLS PIPELINE II=1 

            if(pxi_index == 0) {
                //wait for ctrl signal per batch
                drop_tmp = ctrl_drop.read();
            }
            //read in intermediate fm every time
            //data_tmp = in.read();
            cache = in.read();

            if ((drop_tmp.data == 1 && !drop_mode) || (drop_tmp.data == 0 && drop_mode)) {
                //either drop or pass thru data read
                out_var.batchid = drop_tmp.batchid;
                out_var.data = cache;
                out.write(out_var);
            }
            //else do nothing with data 
        }
    }

    // in the case that the last sample is difficult:
    // still need to perform the flush TODO
    flush_loop: 
    for(unsigned long pxi_index=0;pxi_index<2*buff_size;pxi_index++) {
        #pragma HLS PIPELINE II=1 
        //penultimate sample will either be data or flush the pipeline
        out_var.batchid = 420;
        out_var.data = 6.9;
        out.write(out_var);
    }
}
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    bool         DROP_MODE, //true = drop on 1, false = drop on 0
    typename     buffer_t
>
void buffer(
    stream_t(buffer_t) &in, //might need a float version too
    stream_t(b_bool_t) &ctrl_drop, 
    stream_t(buffer_t) &out
)
{
    #pragma HLS DATAFLOW
    #pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;
    const bool drop_mode          = DROP_MODE;

    //TODO add template value for buffer size
    const unsigned int buff_size  = rows*cols*channels;
    // FIXME this is huge buffering and not realistic
    // FIXME 20x is for the 90rsc version
    const unsigned int depth_in = (20*buff_size)+8;
    //batch_size*buff_size;

    stream_t(b_bool_t) cd_buff;
    stream_t(data_t) in_buff;

    //should prevent stalling first exit FIXME limited to one sample bc other stream
    #pragma HLS STREAM variable=cd_buff depth=batch_size
    //should buffer at least one fm, should prevent deadlock at least 
    #pragma HLS STREAM variable=in_buff depth=depth_in

    buffer_buff<
        BATCH_SIZE,
        1, //rows
        1, //cols
        1, //channels
        b_bool_t
    >(ctrl_drop, cd_buff);

    buffer_buff<
        BATCH_SIZE,
        ROWS, //rows
        COLS, //cols
        CHANNELS, //channels
        buffer_t,
        data_t
    >(in, in_buff);

    buffer_conditional<
        BATCH_SIZE,
        ROWS, //rows
        COLS, //cols
        CHANNELS, //channels
        DROP_MODE,
        buffer_t,
        data_t
    >(in_buff, cd_buff, out);


    ////TODO add template value for buffer size
    //const unsigned int buff_size  = rows*cols*channels;
    //// FIXME this is huge buffering and not realistic
    //const unsigned int in_size  = batch_size*buff_size;

    ////should buffer at least one fm, should prevent deadlock at least 
    //#pragma HLS STREAM variable=in depth=in_size //buff_size
    //#pragma HLS STREAM variable=out
    ////should prevent stalling first exit FIXME limited to one sample bc other stream
    //#pragma HLS STREAM variable=ctrl_drop depth=batch_size

    //b_bool_t drop_tmp;
    //buffer_t data_tmp;

    //batch_loop: for(unsigned long b_index=0;b_index<batch_size;b_index++) {
    //    samp_loop: for(unsigned long pxi_index=0;pxi_index<buff_size;pxi_index++) {
    //    #pragma HLS PIPELINE II=1 

    //        if(pxi_index == 0) {
    //            //wait for ctrl signal per batch
    //            drop_tmp = ctrl_drop.read();
    //        }
    //        //read in intermediate fm every time
    //        data_tmp = in.read();

    //        if ((drop_tmp.data == 1 && !drop_mode) || (drop_tmp.data == 0 && drop_mode)) {
    //            assert(drop_tmp.batchid == data_tmp.batchid);
    //            //either drop or pass thru data read
    //            out.write(data_tmp);
    //        }
    //        //else do nothing with data 
    //    }
    //}

}

/* THE TROUBLESOME HUGE RSC VERSION */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    bool         DROP_MODE, //true = drop on 1, false = drop on 0
    typename     buffer_t
>
void buffer_big(
    stream_t(buffer_t) &in, //might need a float version too
    stream_t(b_bool_t) &ctrl_drop, 
    stream_t(buffer_t) &out
)
{
    #pragma HLS DATAFLOW
    #pragma HLS INLINE OFF

    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;
    const bool drop_mode          = DROP_MODE;

    //TODO add template value for buffer size
    const unsigned int buff_size  = rows*cols*channels;
    // FIXME this is huge buffering and not realistic
    //const unsigned int depth_in = (10*buff_size)+8;
    //batch_size*buff_size;

    stream_t(b_bool_t) cd_buff;
    //stream_t(buffer_t) in_buff[batch_size];
    stream_t(data_t) in_buff[batch_size];

    //should prevent stalling first exit FIXME limited to one sample bc other stream
    #pragma HLS STREAM variable=cd_buff depth=batch_size
    //should buffer at least one fm, should prevent deadlock at least 
    #pragma HLS STREAM variable=in_buff depth=buff_size

    buffer_buff<
        BATCH_SIZE,
        1, //rows
        1, //cols
        1, //channels
        b_bool_t
    >(ctrl_drop, cd_buff);

    buffer_buff_bsplit<
        BATCH_SIZE,
        ROWS, //rows
        COLS, //cols
        CHANNELS, //channels
        buffer_t,
        data_t
    >(in, in_buff);

    buffer_big_conditional<
        BATCH_SIZE,
        ROWS, //rows
        COLS, //cols
        CHANNELS, //channels
        DROP_MODE,
        buffer_t
    >(in_buff, cd_buff, out);

}

#endif
