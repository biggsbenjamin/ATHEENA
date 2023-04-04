#ifndef SOFTMAX_SUM_HPP_ 
#define SOFTMAX_SUM_HPP_ 

#include "common.hpp"

/* EXAMPLE
        // fp adders are complicated
        float acc_part[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        for (int i = 0; i < 32; i += 4) { // Manually unroll by 4
            for (int j = 0; j < 4; j++) { // Partial accumulations
#pragma HLS pipeline
                acc_part[j] += x[i + j];
            }
        for (int i = 1; i < 4; i++) { // Final accumulation
#pragma HLS unroll
            acc_part[0] += acc_part[i];
        }
        // result = acc_part[0];
        // fp adders are complicated
*/

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename sfmsm_t
>
void data_streamer(
    stream_t(sfmsm_t) &in,
    stream_t(sfmsm_t) partials[4]
){
//#pragma HLS INLINE OFF
    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;

    const unsigned int shape_size = rows*cols*channels;
    const unsigned int px_lim = shape_size;//*batch_size;
    //TODO coarse grain folding possibly    
    const unsigned int depth_in = shape_size+20;
    #pragma HLS STREAM variable=in depth=depth_in
    
    // needs to run to nearest multiple of 4...
    // write zeroes for the rest
    sfmsm_t cache, out_var;
    sfmsm_t mid_part[4];

    batch_loop: for (unsigned long batch_index=0;batch_index<batch_size;batch_index++ ) {
        pixel_loop: for(long px_idx=0;px_idx<px_lim+(px_lim%4);px_idx++) {
#pragma HLS pipeline II=1
        if (px_idx < px_lim) {
            cache = in.read();
            out_var.batchid = cache.batchid;
            out_var.data = cache.data;
        } else {
            out_var.data = 0.0;
        }

        int j = px_idx%4;

        //mid_part[j]

        partials[j].write(out_var);
        printf("id: %d, partials:%f\n", out_var.batchid,out_var.data);
        }
    }
}

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename sfmsm_t
>
void partial_accum(
    stream_t(sfmsm_t) in[4],
    stream_t(sfmsm_t) &out
){
//#pragma HLS INLINE OFF
    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;

    const unsigned int shape_size = rows*cols*channels;
    const unsigned int px_lim = (shape_size+(shape_size%4))/4 ;//*batch_size;

    sfmsm_t partial[4];

    batch_loop: for (unsigned long batch_index=0;batch_index<batch_size;batch_index++ ) {
        pixel_loop: for(long px_idx=0;px_idx<px_lim;px_idx++) {
        #pragma HLS pipeline II=8
            part_loop: for (unsigned int pidx=0;pidx<4;pidx++) {
            #pragma HLS unroll
                partial[pidx] += in[pidx].read();
            }
            //acc_loop: for (unsigned int aidx=1;aidx<4;aidx++) {
            //    partial[0].data += partial[aidx].data;
            //}

        //if (px_idx < px_lim) {
        //    cache = in.read();
        //    out_var.batchid = cache.batchid;
        //    out_var.data = cache.data;
        //} else {
        //    out_var.data = 0.0;
        //}

        //partials[j].write(out_var);
        //}
        }
        out.write(partial[0]);
    }
}


template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename sfmsm_t
>
void softmax_sum(
    stream_t(sfmsm_t) &in,
    stream_t(sfmsm_t) &out
)
{

    #pragma HLS INLINE OFF 
    
    const unsigned int batch_size = BATCH_SIZE;
    const unsigned int rows       = ROWS;
    const unsigned int cols       = COLS;
    const unsigned int channels   = CHANNELS;

    const unsigned int shape_size = rows*cols*channels;
    const unsigned int px_lim = shape_size;//*batch_size;
    //TODO coarse grain folding possibly    
    const unsigned int depth_in = shape_size + 40; //(pipeline+1)
    #pragma HLS STREAM variable=in depth=depth_in
    #pragma HLS STREAM variable=out

    //stream_t(sfmsm_t) mid[4];
    //#pragma HLS STREAM variable=mid depth=depth_in

    //data_streamer<
    //    BATCH_SIZE,
    //    ROWS,
    //    COLS,
    //    CHANNELS,
    //    sfmsm_t
    //>(in,mid);

    //partial_accum<
    //    BATCH_SIZE,
    //    ROWS,
    //    COLS,
    //    CHANNELS,
    //    sfmsm_t
    //>(mid,out);

    //const unsigned int partial_num = 8;
    
    // FIXME works but II of 8
    // FIXME UPDATE - VERSION WORKS BUT ONLY FOR 10 classes
    //sfmsm_t cache,sum,tmp;
    sfmsm_t cache[2],sum;
    batch_t b_id;
    //float tmp_f;//, partial[partial_num];
    //float partial[partial_num];
    //#pragma HLS ARRAY_PARTITION variable=partial complete dim=0

    sfmsm_t tree[9];
    //unsigned int partial_sum_count = (px_lim+(px_lim%partial_num))/partial_num;
    //printf("partial sum count:%d\n",partial_sum_count);

    batch_loop: 
    for (unsigned long batch_index=0;batch_index<batch_size;batch_index++ ) {
        //for (int offset=0;offset<partial_num;offset++) {
        //    #pragma HLS unroll
        //    partial[offset] = 0.0f;
        //}
        //pixel_loop: for(unsigned long px_idx=0;px_idx<px_lim+(px_lim%partial_num);px_idx++) {
        //pixel_loop: for(unsigned long px_idx=0;px_idx<px_lim;px_idx++) {
        #pragma HLS PIPELINE II=10 // II 1 not possible (fp add)
        cache[0] = in.read();
        b_id = cache[0].batchid;
        cache[1] = in.read();
        tree[0].data = cache[0].data + cache[1].data;

        cache[0] = in.read();
        cache[1] = in.read();
        tree[1].data = cache[0].data + cache[1].data;

        cache[0] = in.read();
        cache[1] = in.read();
        tree[2].data = cache[0].data + cache[1].data;
        cache[0] = in.read();
        cache[1] = in.read();
        tree[3].data = cache[0].data + cache[1].data;
        cache[0] = in.read();
        cache[1] = in.read();
        tree[4].data = cache[0].data + cache[1].data;

        tree[5].data = tree[0].data + tree[1].data;
        tree[6].data = tree[2].data + tree[3].data;

        tree[7].data = tree[5].data + tree[4].data;
        tree[8].data = tree[6].data + tree[7].data;

        sum.batchid = b_id;
        sum.data = tree[8].data;

            //// read in new value every cycle
            //if (px_idx < px_lim) {
            //    cache = in.read();
            //    tmp_f = cache.data; 
            //} else {
            //    // for sums that arent div by partial_num, add zeroes
            //    tmp_f = 0.0f; 
            //}
            //// read batch off of first sample
            //if (px_idx == 0) {
            //    b_id = cache.batchid;
            //}

            ////printf("tmp f: %f\n",tmp_f);
            //int pidx = px_idx % partial_num;     // 0,1,2,3,0,1...
            //for (int offset=0;offset<partial_num;offset++) {
            //    #pragma HLS unroll
            //    if (pidx == offset) {
            //        #pragma HLS occurrence cycle=partial_num
            //        partial[offset] += tmp_f;
            //    }
            //}
            //
            ////printf("partial0:%f, partial1:%f, partial2:%f, partial2:%f\n",
            ////        partial[0],partial[1],partial[2],partial[3]);

        //    // FIXME working but crap version
        //    cache=in.read();
        //    tmp.data = sum.data + cache.data;

        //    if (px_idx == 0)
        //        //restart sum at the beginning of new shape
        //        sum.data = cache.data;
        //    else 
        //        sum.data = tmp.data;
        //    sum.batchid=cache.batchid;
        //}
        //// final accumulation of partial sums
        //for (int fa_idx=1; fa_idx<partial_num; fa_idx++) {
        //    #pragma HLS unroll
        //    partial[0] += partial[fa_idx];
        //}
        //// assign final sum and batch id
        //sum.data = partial[0];
        //sum.batchid = b_id;

        out.write(sum);
    }
}

#endif
