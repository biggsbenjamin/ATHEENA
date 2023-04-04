#ifndef REDMAX_HPP_
#define REDMAX_HPP_

#include "common.hpp"

//template<
//    unsigned int BATCH_SIZE,
//    unsigned int ROWS,
//    unsigned int COLS,
//    unsigned int CHANNELS,
//    typename rdmx_t
//>
//void master_splinter(
//    stream_t(rdmx_t) &in,
//    stream_t(rdmx_t) split[2]
//)
//{
//#pragma HLS INLINE OFF 
//
//    const unsigned int batch_size   = BATCH_SIZE;
//    const unsigned int rows         = ROWS;
//    const unsigned int cols         = COLS;
//    const unsigned int channels     = CHANNELS;
//    const unsigned int px_lim = rows*cols*channels;
//    const unsigned int depth_in = px_lim+8; 
//    #pragma HLS STREAM variable=in depth=depth_in
//    #pragma HLS STREAM variable=split
//    #pragma HLS ARRAY_PARTITION variable=split complete dim=0
//
//    rdmx_t tmp;
//    
//    batch_loop: 
//    for(unsigned long batch_index=0;batch_index<batch_size;batch_index++) {
//        pixel_loop:
//        for (unsigned long px_index = 0; px_index < px_lim+(px_lim%4); px_index++) {
//            #pragma HLS PIPELINE II=1 rewind
//            if (px_index < px_lim){
//                tmp = in.read();
//            }
//
//            int count4 = px_index%4; 
//            if (count4 == 0 || count4 == 1) {
//                printf("split0 out: %d %f\n",tmp.batchid,tmp.data);
//                split[0].write(tmp);
//            } else {
//                printf("split1 out: %d %f\n",tmp.batchid,tmp.data);
//                split[1].write(tmp);
//            }
//        }
//    }
//}
//
//template<
//    unsigned int BATCH_SIZE,
//    unsigned int ROWS,
//    unsigned int COLS,
//    unsigned int CHANNELS,
//    unsigned int DIV,
//    typename rdmx_t
//>
//void fp_cmp(
//    stream_t(rdmx_t) &split_in,
//    stream_t(rdmx_t) &out 
//)
//{
//#pragma HLS INLINE OFF 
//
//    const unsigned int batch_size   = BATCH_SIZE;
//    const unsigned int rows         = ROWS;
//    const unsigned int cols         = COLS;
//    const unsigned int channels     = CHANNELS;
//    const unsigned int div         = DIV;
//    const unsigned int px_lim = rows*cols*channels;
//    const unsigned int depth_in = px_lim+8; 
//    rdmx_t a,b,out_var;
//
//    #pragma HLS STREAM variable=split_in depth=6
//    #pragma HLS STREAM variable=out
//
//    batch_loop: 
//    for(unsigned long batch_index=0;batch_index<batch_size;batch_index++) {
//        pixel_loop:
//        for (unsigned long px_index = 0; px_index < (px_lim+(px_lim%4))/DIV; px_index++) {
//            #pragma HLS PIPELINE II=1 rewind
//            a = split_in.read(); 
//            b = split_in.read(); 
//
//            if (a.data > b.data) {
//                out_var.data = a.data;
//            } else {
//                out_var.data = b.data;
//            }
//
//            out_var.batchid = a.batchid;
//            out.write(out_var); 
//        }
//    }
//}
//
//template<
//    unsigned int BATCH_SIZE,
//    unsigned int ROWS,
//    unsigned int COLS,
//    unsigned int CHANNELS,
//    typename rdmx_t
//>
//void master_merger(
//    stream_t(rdmx_t) split[2],
//    stream_t(rdmx_t) &out
//)
//{
//#pragma HLS INLINE OFF 
//
//    const unsigned int batch_size   = BATCH_SIZE;
//    const unsigned int rows         = ROWS;
//    const unsigned int cols         = COLS;
//    const unsigned int channels     = CHANNELS;
//    const unsigned int px_lim = rows*cols*channels;
//    const unsigned int depth_in = px_lim+8; 
//    #pragma HLS STREAM variable=in 
//    #pragma HLS STREAM variable=split
//    #pragma HLS ARRAY_PARTITION variable=split complete dim=0
//
//    rdmx_t tmp;
//    
//    batch_loop: 
//    for(unsigned long batch_index=0;batch_index<batch_size;batch_index++) {
//        pixel_loop:
//        for (unsigned long px_index = 0; px_index < (px_lim+(px_lim%4))/2; px_index++) {
//            #pragma HLS PIPELINE II=1 rewind
//            //if (px_index < px_lim){
//            //    tmp = in.read();
//            //}
//            int j = px_index%2;
//            
//            tmp = split[j].read();
//            out.write(tmp);
//
//            //int count4 = px_index%4; 
//            //if (count4 == 0 || count4 == 1) {
//            //    split[0].write(tmp);
//            //} else {
//            //    split[1].write(tmp);
//            //}
//        }
//    }
//}

/**
  * REDUCE MAX 
  */
template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    typename rdmx_t
>
void reducemax(
    stream_t(rdmx_t) &in,
    stream_t(rdmx_t) &out
    //hls::stream<float> &in,
    //hls::stream<float> &out
)
{

#pragma HLS INLINE OFF 

    const unsigned int batch_size   = BATCH_SIZE;
    const unsigned int rows         = ROWS;
    const unsigned int cols         = COLS;
    const unsigned int channels     = CHANNELS;
    const unsigned int px_lim = rows*cols*channels;
    const unsigned int depth_in = px_lim+24; //(pipeline+1) 
#pragma HLS STREAM variable=in depth=depth_in
#pragma HLS STREAM variable=out

    //stream_t(rdmx_t) split[2];
    //#pragma HLS STREAM variable=split depth=6 
    //#pragma HLS ARRAY_PARTITION variable=split complete dim=0
    //stream_t(rdmx_t) mid_out[2];
    //#pragma HLS STREAM variable=mid_out depth=6 
    //#pragma HLS ARRAY_PARTITION variable=mid_out complete dim=0
    //stream_t(rdmx_t) comb;

    //master_splinter<
    //    BATCH_SIZE,
    //    ROWS,
    //    COLS,
    //    CHANNELS,
    //    rdmx_t
    //>(in,split);

    //for (int i=0;i<2;i++){
    //    #pragma HLS unroll
    //    fp_cmp<
    //        BATCH_SIZE,
    //        ROWS,
    //        COLS,
    //        CHANNELS,
    //        2,
    //        rdmx_t
    //    >(split[i],mid_out[i]);
    //}

    //master_merger<
    //    BATCH_SIZE,
    //    ROWS,
    //    COLS,
    //    CHANNELS,
    //    rdmx_t
    //>(mid_out,comb);

    //fp_cmp<
    //    BATCH_SIZE,
    //    ROWS,
    //    COLS,
    //    CHANNELS,
    //    4,
    //    rdmx_t
    //>(comb,out);

    // FIXME simple to code version but bad latency
    //rdmx_t cache,tmp;
    ////float cache,tmp;

    //batch_loop: for(unsigned long batch_index=0;batch_index<batch_size;batch_index++) {
    //    pixel_loop: for (unsigned long px_index = 0; px_index < px_lim; px_index++) {
    //        #pragma HLS PIPELINE II=1 rewind
    //        cache = in.read();
    //        //std::cout<<"rdmx,in cache: "<<cache.data<<std::endl;
    //        if (px_index == 0) {
    //            tmp.data = cache.data;
    //        } else {
    //            tmp.data = (cache.data > tmp.data ) ? cache.data : tmp.data;
    //        }
    //        tmp.batchid = cache.batchid;
    //    }
    //    //std::cout<<"rdmx,out: "<<tmp.data<< " ID:"<<tmp.batchid<<std::endl;
    //    out.write(tmp);
    //}

    // FIXME more resources and fixed input size of 10 classes
    rdmx_t max_val, cache[2], tree[9];
    batch_t b_id;

    batch_loop: 
    for (unsigned long batch_index=0;batch_index<batch_size;batch_index++ ) {
        #pragma HLS PIPELINE II=10 // II 1 not possible (fp cmp)
        cache[0] = in.read();
        b_id = cache[0].batchid;
        cache[1] = in.read();
        tree[0].data = (cache[0].data > cache[1].data) ? cache[0].data : cache[1].data;

        cache[0] = in.read();
        cache[1] = in.read();
        tree[1].data = (cache[0].data > cache[1].data) ? cache[0].data : cache[1].data;

        cache[0] = in.read();
        cache[1] = in.read();
        tree[2].data = (cache[0].data > cache[1].data) ? cache[0].data : cache[1].data;
        cache[0] = in.read();
        cache[1] = in.read();
        tree[3].data = (cache[0].data > cache[1].data) ? cache[0].data : cache[1].data;
        cache[0] = in.read();
        cache[1] = in.read();
        tree[4].data = (cache[0].data > cache[1].data) ? cache[0].data : cache[1].data;

        tree[5].data = (tree[0].data > tree[1].data) ? tree[0].data : tree[1].data;
        tree[6].data = (tree[2].data > tree[3].data) ? tree[2].data : tree[3].data;

        tree[7].data = (tree[5].data > tree[4].data) ? tree[5].data : tree[4].data;
        tree[8].data = (tree[6].data > tree[7].data) ? tree[6].data : tree[7].data;

        max_val.batchid = b_id;
        max_val.data = tree[8].data;

        out.write(max_val);
    }
}

#endif
