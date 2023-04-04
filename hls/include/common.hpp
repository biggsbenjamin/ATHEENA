#ifndef COMMON_HPP_
#define COMMON_HPP_

#include "system.hpp"
#include <ap_fixed.h>
#include <ap_int.h>
#include "hls_stream.h"
#include "hls_math.h"
#include "ap_axi_sdata.h"
#include "stdint.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>


#define ERROR_TOLERANCE 0.2//1.0

// MACRO FOR TEMPLATE VARIABLE PRAGMAS
#define PRAGMA_SUB(x) _Pragma (#x)
#define DO_PRAGMA(x) PRAGMA_SUB(x)

#define NAME_SUB(a,b)           NAME_SUB_HIDDEN(a,b)
#define NAME_SUB_HIDDEN(a,b)    a ## b

#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)

#define DIVIDE(a,b) ((int) ((a)/(b)))
// LAYER OPERATIONS
#define FILTERS_PER_UNIT_3D(filters,channels,coarse_in,coarse_out)    ((int) ((filters*channels)/(coarse_in*coarse_out)))
#define FILTERS_3D(filters,coarse_in,coarse_out)    ((int) (filters/(coarse_in*coarse_out)))
#define CHANNELS_3D(channels,coarse_in)             ((int) (channels/coarse_in))
#define FILTERS_PER_UNIT(filters,coarse)    ((int) (filters/coarse))

#define LAYER_ROWS_OUT(rows,k_size,stride,pad)    ((int)(rows-k_size+2*pad)/stride+1)
#define LAYER_COLS_OUT(cols,k_size,stride,pad)    ((int)(cols-k_size+2*pad)/stride+1)

#define GET_SW_ROWS_OUT(rows,k_size,stride,pad_top,pad_bottom)    ((int)(rows-k_size+pad_top+pad_bottom)/stride+1)
#define GET_SW_COLS_OUT(cols,k_size,stride,pad_left,pad_right)    ((int)(cols-k_size+pad_left+pad_right)/stride+1)
#define GET_SW_CHANNELS_OUT(channels,stride)                      ((int)(channels/stride))

#define FILTERS_WEIGHT_RELOADING(filters,factor) ((int)(filters/factor))

#define CONV_HW_II(fine,k_size)             ((int)((k_size*k_size)/fine))

#define MIN(a,b) (((a)<(b))?(a):(b))

#define SWITCHING_ACTIVITY_DEBUG 0

// DATA TYPE PARAMETERS
#define DATA_WIDTH   16
#define INTEGER_BITS 8
#define BIT_MASK    ( (1 << DATA_WIDTH) - 1 )


#define DMA_WIDTH         64
#define STREAMS_PER_PORT  ((int)DMA_WIDTH/DATA_WIDTH)

// DATA TYPES
#if DMA_WIDTH == 64
typedef unsigned long mem_int;
#else
typedef unsigned int mem_int;
#endif
typedef ap_axis<DMA_WIDTH,1,1,1>    axi_stream_t;
typedef hls::stream<axi_stream_t>   axi_stream_hw_t;


//typedef ap_fixed<DATA_WIDTH,INTEGER_BITS,AP_RND> data_t;
typedef ap_fixed<16,8,AP_RND> data_t;
typedef ap_fixed<30,16,AP_RND> acc_t;
typedef ap_fixed<16,8,AP_RND> weight_t;
//typedef ap_fixed<10,2,AP_RND> weight_t;

//typedef ap_fixed<64,32> bdata_t;

typedef ap_uint<16> batch_t;

//axi stream experiment
//typedef ap_axiu<16,0,0,0> axis_t;
struct axis_t {
    data_t data;
    ap_int<1> last;
};
typedef hls::stream<axis_t>   axis_hls_t;
//axi stream experiment

// batch id included data types
struct b_data_t {
    batch_t batchid;
    data_t data;
};
struct b_acc_t {
    batch_t batchid;
    acc_t data;
};
struct b_float_t {
    batch_t batchid;
    float data;
};
struct b_bool_t {
    batch_t batchid;
    bool data;
};
//struct b_axis_t {
//    b_data_t samp;
//    ap_int<1> last;
//};
//typedef hls::stream<b_axis_t>   b_axis_hls_t;
struct axis32_t {
    ap_uint<32> sample;
    ap_int<1> last;
};
typedef hls::stream<axis32_t>   axis32_strm_t;


//#define stream_t(x) hlslib::Stream<x>
#define stream_t(x) hls::stream<x>

#endif
