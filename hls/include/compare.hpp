#ifndef CMP_HPP_
#define CMP_HPP_

#include "common.hpp"

/**
  * EXIT COMPARE
  */
template<
    unsigned int BATCH_SIZE,
    //unsigned int ROWS,
    //unsigned int COLS,
    //unsigned int CHANNELS,
    typename cmp_t,
    typename ctrl_t
>
void compare(
    stream_t(cmp_t) &max_in,
    stream_t(cmp_t) &thr_in,
    //hls::stream<float> &max_in,
    //hls::stream<float> &thr_in,
    float thr_val[1],
    stream_t(ctrl_t) &ctrl_out
)
{

#pragma HLS INLINE OFF 

    const unsigned int batch_size   = BATCH_SIZE;
    //const unsigned int rows         = ROWS;
    //const unsigned int cols         = COLS;
    //const unsigned int channels     = CHANNELS;
    const float threshold = thr_val[0];
    const unsigned int depth_in = batch_size + 16;
 
#pragma HLS STREAM variable=max_in depth=depth_in
#pragma HLS STREAM variable=thr_in depth=depth_in
#pragma HLS STREAM variable=ctrl_out

    //TODO:
    //comparison against threshold value
    //maybe multiply threshold by sftmx sum
    //output ctrl signals to relevant buffer modu + exit select mod
    //  needs to be done synchronously with result?
    //synchronise with batch id pipeline
    //TODO - consider later exits will be ctrl dependent, unknown number of iterations
    //  might make sense to have two versions (in this file)

    cmp_t thr_mult, thr_res, cmp_max;
    ctrl_t out_var;
    
    batch_loop: for(unsigned long b_index=0;b_index<batch_size;b_index++) {
        #pragma HLS PIPELINE II=1
        thr_mult = thr_in.read(); //this one will arrive later
        thr_res.data = thr_mult.data * threshold;
        cmp_max = max_in.read();
        out_var.batchid = thr_mult.batchid;
        //std::cout<<"sfmsm,thr_res: "<<thr_res.data<<" cmp_max:"<<cmp_max.data<<std::endl;
        if (cmp_max.data >= thr_res.data) {
            //exit should occur
            out_var.data = true;
        } else {
            //no exit for this batch item
            out_var.data = false;
        }
        //std::cout<<"cmp out: "<<out_var.data<< " ID:"<<out_var.batchid<<std::endl;
        ctrl_out.write(out_var);
    }
}

#endif
