#ifndef CONV_HPP_
#define CONV_HPP_

#include "common.hpp"

/**
 *  CONVOLUTION FUNCTION A
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t
>
void conv_intr_inner(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE],
    conv_data_t window_cache[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    unsigned int filter_index,
    unsigned int weight_index
)
{

#pragma HLS INLINE
    //printf("Conv version A, conv_intr_inner\n");

    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int filters       = FILTERS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

    // fine index
    unsigned char fine_index = 0;
    intr_k2_loop: for(unsigned char k2=0;k2<kernel_size_y;k2++) {
        intr_k1_loop: for(unsigned char k1=0;k1<kernel_size_x;k1++) {

            // read into the window cache
            if(filter_index%filters_per_group == 0) {
                window_cache[k1][k2] = in[k1][k2].read();
            }

            // write to the window and weights streams
            window_stream[fine_index].write(window_cache[k1][k2]);
            weight_stream[fine_index].write(weights[weight_index][k1][k2]);

            // increment the fine index
            fine_index = ( fine_index + 1 ) % fine;
        }
    }
}

/**
 *  conv intr B
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FILTERS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t
>
void conv_intr(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE]
)
{

#pragma HLS INLINE OFF

    printf("Conv version B, conv intr full\n");
    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int filters       = FILTERS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream

#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0

    // partition the weights correctly
    const unsigned int weights_partition_factor_k1 = MIN(fine,kernel_size_x);
    const unsigned int weights_partition_factor_k2 = (fine<=kernel_size_x) ? 1 : kernel_size_y;

DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k1 dim=2)
DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k2 dim=3)

    // window cache
    conv_data_t window_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=window_cache complete dim=0
    #pragma HLS dependence variable=window_cache intra RAW true
    DO_PRAGMA( HLS dependence variable=window_cache inter WAW true distance=batch_size*rows*cols*channels )

    for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        unsigned int weight_index = 0;
        for(unsigned int channel_index=0;channel_index<channels_per_group;channel_index++) {
            for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
                #pragma HLS loop_flatten
                DO_PRAGMA( HLS PIPELINE II=interval )
                conv_intr_inner<BATCH_SIZE, ROWS, COLS, CHANNELS, FILTERS,
                    GROUPS, FINE, KERNEL_SIZE_X, KERNEL_SIZE_Y,
                    conv_data_t, conv_weight_t>(in, weights, window_stream,
                            weight_stream, window_cache, filter_index, weight_index);
                weight_index++;
            }
        }
    }
}

/**
 *  conv intr C
 *  - single channel per group
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FILTERS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t
>
void conv_intr(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE]
)
{

#pragma HLS INLINE OFF

    printf("Conv version C, conv intr single ch p grp\n");
    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int filters       = FILTERS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream

#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0

    // partition the weights correctly
    const unsigned int weights_partition_factor_k1 = MIN(fine,kernel_size_x);
    const unsigned int weights_partition_factor_k2 = (fine<=kernel_size_x) ? 1 : kernel_size_y;

DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k1 dim=2)
DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k2 dim=3)

    // window cache
    conv_data_t window_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=window_cache complete dim=0
    #pragma HLS dependence variable=window_cache intra RAW true
    DO_PRAGMA( HLS dependence variable=window_cache inter WAW true distance=batch_size*rows*cols*channels )

    for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        unsigned int weight_index = 0;
        for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
            #pragma HLS loop_flatten
            DO_PRAGMA( HLS PIPELINE II=interval )
            conv_intr_inner<BATCH_SIZE, ROWS, COLS, CHANNELS, FILTERS,
                GROUPS, FINE, KERNEL_SIZE_X, KERNEL_SIZE_Y,
                conv_data_t, conv_weight_t>(in, weights, window_stream,
                        weight_stream, window_cache, filter_index, weight_index);
            weight_index++;
        }
    }
}

/**
 *  conv intr D
 *  - single filter
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t
>
void conv_intr(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[DIVIDE(CHANNELS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE]
)
{

#pragma HLS INLINE OFF

    printf("Conv version D, conv intr single fil\n");
    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = DIVIDE(channels,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream

#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0

    // partition the weights correctly
    const unsigned int weights_partition_factor_k1 = MIN(fine,kernel_size_x);
    const unsigned int weights_partition_factor_k2 = (fine<=kernel_size_x) ? 1 : kernel_size_y;

DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k1 dim=2)
DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k2 dim=3)

    // window cache
    conv_data_t window_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=window_cache complete dim=0
    #pragma HLS dependence variable=window_cache intra RAW true
    DO_PRAGMA( HLS dependence variable=window_cache inter WAW true distance=batch_size*rows*cols*channels )

    for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        unsigned int weight_index = 0;
        for(unsigned int channel_index=0;channel_index<channels_per_group;channel_index++) {
            #pragma HLS loop_flatten
            DO_PRAGMA( HLS PIPELINE II=interval )
            conv_intr_inner<BATCH_SIZE, ROWS, COLS, CHANNELS, 1,
                GROUPS, FINE, KERNEL_SIZE_X, KERNEL_SIZE_Y,
                conv_data_t, conv_weight_t>(in, weights, window_stream,
                        weight_stream, window_cache, 0, weight_index);
            weight_index++;
        }
    }
}

/**
 *  conv intr E
 *  - single filter
 *  - single channel per group
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename hack
>
void conv_intr(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[1][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE]
)
{

#pragma HLS INLINE OFF

    printf("Conv version E, conv intr, 1 fil, 1 ch per grp\n");
    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = 1;

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream

#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0

    // partition the weights correctly
    const unsigned int weights_partition_factor_k1 = MIN(fine,kernel_size_x);
    const unsigned int weights_partition_factor_k2 = (fine<=kernel_size_x) ? 1 : kernel_size_y;

DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k1 dim=2)
DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k2 dim=3)

    // window cache
    conv_data_t window_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=window_cache complete dim=0
    #pragma HLS dependence variable=window_cache intra RAW true
    DO_PRAGMA( HLS dependence variable=window_cache inter WAW true distance=batch_size*rows*cols*channels )

    for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        unsigned int weight_index = 0;
        DO_PRAGMA( HLS PIPELINE II=interval )
        conv_intr_inner<BATCH_SIZE, ROWS, COLS, CHANNELS, 1,
            GROUPS, FINE, KERNEL_SIZE_X, KERNEL_SIZE_Y,
            conv_data_t, conv_weight_t>(in, weights, window_stream,
                    weight_stream, window_cache, 0, weight_index);
        weight_index++;
    }
}

/**
 *  conv intr F
 *  - single iteration
 */

template<
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FILTERS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t
>
void conv_intr(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE]
)
{

#pragma HLS INLINE OFF

    printf("Conv version F, conv intr, 1 iter\n");
    const unsigned int channels      = CHANNELS;
    const unsigned int filters       = FILTERS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream

#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0

    // partition the weights correctly
    const unsigned int weights_partition_factor_k1 = MIN(fine,kernel_size_x);
    const unsigned int weights_partition_factor_k2 = (fine<=kernel_size_x) ? 1 : kernel_size_y;

DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k1 dim=2)
DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k2 dim=3)

    // window cache
    conv_data_t window_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=window_cache complete dim=0
    #pragma HLS dependence variable=window_cache intra RAW true
    DO_PRAGMA( HLS dependence variable=window_cache inter WAW true distance=channels )

    unsigned int weight_index = 0;
    for(unsigned int channel_index=0;channel_index<channels_per_group;channel_index++) {
        for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
            #pragma HLS loop_flatten
            DO_PRAGMA( HLS PIPELINE II=interval )
            conv_intr_inner<1, 1, 1, CHANNELS, FILTERS,
                GROUPS, FINE, KERNEL_SIZE_X, KERNEL_SIZE_Y,
                conv_data_t, conv_weight_t>(in, weights, window_stream,
                        weight_stream, window_cache, filter_index, weight_index);
            weight_index++;
        }
    }
}

/**
 *  conv intr G
 *  - single iteration
 *  - single channel per group
 */

template<
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FILTERS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t
>
void conv_intr(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE]
)
{

#pragma HLS INLINE OFF

    printf("Conv version G, conv intr, 1 iter, 1 ch per grp\n");
    const unsigned int channels      = CHANNELS;
    const unsigned int filters       = FILTERS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream

#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0

    // partition the weights correctly
    const unsigned int weights_partition_factor_k1 = MIN(fine,kernel_size_x);
    const unsigned int weights_partition_factor_k2 = (fine<=kernel_size_x) ? 1 : kernel_size_y;

DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k1 dim=2)
DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k2 dim=3)

    // window cache
    conv_data_t window_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=window_cache complete dim=0
    #pragma HLS dependence variable=window_cache intra RAW true
    DO_PRAGMA( HLS dependence variable=window_cache inter WAW true distance=channels )

    unsigned int weight_index = 0;
    for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
        DO_PRAGMA( HLS PIPELINE II=interval )
        conv_intr_inner<1, 1, 1, CHANNELS, FILTERS,
            GROUPS, FINE, KERNEL_SIZE_X, KERNEL_SIZE_Y,
            conv_data_t, conv_weight_t>(in, weights, window_stream,
                    weight_stream, window_cache, filter_index, weight_index);
        weight_index++;
    }
}
/**
 *  conv intr H
 *  - single iteration
 *  - single filter
 */

template<
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t
>
void conv_intr(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[DIVIDE(CHANNELS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE]
)
{

#pragma HLS INLINE OFF

    printf("Conv version H, conv intr, 1 iter, 1 fil\n");
    const unsigned int channels      = CHANNELS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = DIVIDE(channels,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream

#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0

    // partition the weights correctly
    const unsigned int weights_partition_factor_k1 = MIN(fine,kernel_size_x);
    const unsigned int weights_partition_factor_k2 = (fine<=kernel_size_x) ? 1 : kernel_size_y;

DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k1 dim=2)
DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k2 dim=3)

    // window cache
    conv_data_t window_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=window_cache complete dim=0
    #pragma HLS dependence variable=window_cache intra RAW true
    DO_PRAGMA( HLS dependence variable=window_cache inter WAW true distance=channels )

    unsigned int weight_index = 0;
    for(unsigned int channel_index=0;channel_index<channels_per_group;channel_index++) {
        DO_PRAGMA( HLS PIPELINE II=interval )
        conv_intr_inner<1, 1, 1, CHANNELS, 1,
            GROUPS, FINE, KERNEL_SIZE_X, KERNEL_SIZE_Y,
            conv_data_t, conv_weight_t>(in, weights, window_stream,
                    weight_stream, window_cache, 0, weight_index);
        weight_index++;
    }
}

/**
 *  conv intr I
 *  - single iteration
 *  - single filter
 *  - single channel per group
 */

template<
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t
>
void conv_intr(
    stream_t(conv_data_t)    in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t      weights[1][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_data_t)    window_stream[FINE],
    stream_t(conv_weight_t)  weight_stream[FINE]
)
{

#pragma HLS INLINE OFF

    printf("Conv version I, 1 iter, 1 fil, 1 ch per grp\n");
    const unsigned int channels      = CHANNELS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);

    const unsigned int channels_per_group = 1;

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream

#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0

    // partition the weights correctly
    const unsigned int weights_partition_factor_k1 = MIN(fine,kernel_size_x);
    const unsigned int weights_partition_factor_k2 = (fine<=kernel_size_x) ? 1 : kernel_size_y;

DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k1 dim=2)
DO_PRAGMA(HLS ARRAY_PARTITION variable=weights block factor=weights_partition_factor_k2 dim=3)

    // window cache
    conv_data_t window_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=window_cache complete dim=0
    #pragma HLS dependence variable=window_cache intra RAW true
    DO_PRAGMA( HLS dependence variable=window_cache inter WAW true distance=channels )

    unsigned int weight_index = 0;
    DO_PRAGMA( HLS PIPELINE II=interval )
    conv_intr_inner<1, 1, 1, CHANNELS, 1,
        GROUPS, FINE, KERNEL_SIZE_X, KERNEL_SIZE_Y,
        conv_data_t, conv_weight_t>(in, weights, window_stream,
                weight_stream, window_cache, 0, weight_index);
    weight_index++;
}

/**
 *  conv mul K
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv_mul(
    stream_t(conv_data_t) window_stream[FINE],
    stream_t(conv_weight_t) weight_stream[FINE],
    stream_t(conv_acc_t) acc_stream[FINE]
)
{

#pragma HLS INLINE OFF

#pragma HLS STREAM variable=window_stream
#pragma HLS STREAM variable=weight_stream
#pragma HLS STREAM variable=acc_stream

    printf("Conv version K, conv mul\n");
    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int filters       = FILTERS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;
    const unsigned int interval      = DIVIDE(kernel_size_x*kernel_size_y,fine);


    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

#pragma HLS ARRAY_PARTITION variable=window_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=weight_stream complete dim=0
#pragma HLS ARRAY_PARTITION variable=acc_stream    complete dim=0

    // intermediate variables to deal with struct
    conv_data_t win;
    conv_acc_t acc_cache[fine], prev;
    // Setting up a variable of accumulation type that is zero
    conv_acc_t acc_zero;
    acc_zero.data = 0;
    unsigned char acc_index=0;
    // MULTIPLICATION LOOP
    mul_pixel_loop: for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols*channels_per_group*filters_per_group*groups*interval;pixel_index++) {
            #pragma HLS pipeline II=1
            mul_loop: for(unsigned char fine_index=0;fine_index<fine;fine_index++) {
                
                // update accumulation cache
                prev.data = ( acc_index == 0 ) ? acc_zero.data : acc_cache[fine_index].data ;
                win = window_stream[fine_index].read();
                acc_cache[fine_index].data = prev.data+win.data*weight_stream[fine_index].read();
                //set batchid
                acc_cache[fine_index].batchid = win.batchid;
                
                // write to output stream
                if( acc_index == (interval-1) ) {
                    acc_stream[fine_index].write( acc_cache[fine_index] ) ;
                }
            }
            // increment accumulation index
            acc_index = (acc_index+1) % interval;
    }
}

/**
 *  conv acc L
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_acc_t
>
void conv_acc(
    stream_t(conv_acc_t) acc_stream[FINE],
    stream_t(conv_acc_t) &out
)
{

    #pragma HLS INLINE OFF

    #pragma HLS STREAM variable=acc_stream
    #pragma HLS ARRAY_PARTITION variable=acc_stream complete dim=0

    #pragma HLS STREAM variable=out

    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int filters       = FILTERS;
    const unsigned int groups        = GROUPS;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    const unsigned int fine          = FINE;

    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

    conv_acc_t acc,tmp;
    // ACCUMULATION LOOP
    acc_pixel_loop: for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols*channels_per_group*filters_per_group*groups;pixel_index++) {
        #pragma HLS pipeline II=1 rewind
        acc.data=0;
        acc_fine_loop: for(unsigned char fine_index=0;fine_index<fine;fine_index++) {
            tmp = acc_stream[fine_index].read();
            acc.data += tmp.data;
            acc.batchid = tmp.batchid;
        }
        out.write(acc);
    }
}

/**
 *  conv M
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FILTERS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    printf("Conv version M, full conv standard\n");
    const unsigned int fine = FINE;

    stream_t(conv_data_t) window_stream[fine];
    stream_t(conv_weight_t) weight_stream[fine];
    stream_t(conv_acc_t) acc_stream[fine];

    #pragma HLS STREAM variable=window_stream
    #pragma HLS STREAM variable=weight_stream
    #pragma HLS STREAM variable=acc_stream

    conv_intr<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        FILTERS,
        GROUPS,
        CHANNELS_PER_GROUP,
        FILTERS_PER_GROUP,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t
    >(in,weights,window_stream,weight_stream);

    conv_mul<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        FILTERS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        conv_acc_t
    >(window_stream,weight_stream,acc_stream);

    conv_acc<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        FILTERS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_acc_t
    >(acc_stream, out);

}

/**
 *  conv N
 *  - single channel per group
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FILTERS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    printf("Conv version N, full conv, 1 ch per grp\n");
    const unsigned int fine = FINE;

    stream_t(conv_data_t) window_stream[fine];
    stream_t(conv_weight_t) weight_stream[fine];
    stream_t(conv_acc_t) acc_stream[fine];

    #pragma HLS STREAM variable=window_stream
    #pragma HLS STREAM variable=weight_stream
    #pragma HLS STREAM variable=acc_stream

    conv_intr<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        FILTERS,
        GROUPS,
        FILTERS_PER_GROUP,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t
    >(in,weights,window_stream,weight_stream);

    conv_mul<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        FILTERS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        conv_acc_t
    >(window_stream,weight_stream,acc_stream);

    conv_acc<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        FILTERS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_acc_t
    >(acc_stream, out);

}

/**
 *  conv O
 *  - single filter
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t weights[DIVIDE(CHANNELS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    printf("Conv version O, full conv, 1 fil\n");
    const unsigned int fine = FINE;

    stream_t(conv_data_t) window_stream[fine];
    stream_t(conv_weight_t) weight_stream[fine];
    stream_t(conv_acc_t) acc_stream[fine];

    #pragma HLS STREAM variable=window_stream
    #pragma HLS STREAM variable=weight_stream
    #pragma HLS STREAM variable=acc_stream

    conv_intr<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        GROUPS,
        CHANNELS_PER_GROUP,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t
    >(in,weights,window_stream,weight_stream);

    conv_mul<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        1,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        conv_acc_t
    >(window_stream,weight_stream,acc_stream);

    conv_acc<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        1,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_acc_t
    >(acc_stream, out);

}

/**
 *  conv P
 *  - single filter
 *  - single channel per group
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t,
    typename hack
>
void conv(
    stream_t(conv_data_t) in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t weights[DIVIDE(CHANNELS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    printf("Conv version Q, full conv, 1 fil, 1 ch per grp\n");
    const unsigned int fine = FINE;

    stream_t(conv_data_t) window_stream[fine];
    stream_t(conv_weight_t) weight_stream[fine];
    stream_t(conv_acc_t) acc_stream[fine];

    #pragma HLS STREAM variable=window_stream
    #pragma HLS STREAM variable=weight_stream
    #pragma HLS STREAM variable=acc_stream

    conv_intr<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        hack
    >(in,weights,window_stream,weight_stream);

    conv_mul<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        1,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        conv_acc_t
    >(window_stream,weight_stream,acc_stream);

    conv_acc<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        1,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_acc_t
    >(acc_stream, out);

}

/**
 *  conv R
 *  - single iteration
 */

template<
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FILTERS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

//#pragma HLS stable variable=weights


#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    printf("Conv version R, full conv, 1 iter\n");
    const unsigned int fine = FINE;

    stream_t(conv_data_t) window_stream[fine];
    stream_t(conv_weight_t) weight_stream[fine];
    stream_t(conv_acc_t) acc_stream[fine];

    #pragma HLS STREAM variable=window_stream
    #pragma HLS STREAM variable=weight_stream
    #pragma HLS STREAM variable=acc_stream

    conv_intr<
        CHANNELS,
        FILTERS,
        GROUPS,
        CHANNELS_PER_GROUP,
        FILTERS_PER_GROUP,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t
    >(in,weights,window_stream,weight_stream);

    conv_mul<
        1,
        1,
        1,
        CHANNELS,
        FILTERS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        conv_acc_t
    >(window_stream,weight_stream,acc_stream);

    conv_acc<
        1,
        1,
        1,
        CHANNELS,
        FILTERS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_acc_t
    >(acc_stream, out);

}

/**
 *  conv S
 *  - single iteration
 *  - single channel per group
 */

template<
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FILTERS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

//#pragma HLS stable variable=weights


#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    printf("Conv version S, 1 iter, 1 ch per grp\n");
    const unsigned int fine = FINE;

    stream_t(conv_data_t) window_stream[fine];
    stream_t(conv_weight_t) weight_stream[fine];
    stream_t(conv_acc_t) acc_stream[fine];

    #pragma HLS STREAM variable=window_stream
    #pragma HLS STREAM variable=weight_stream
    #pragma HLS STREAM variable=acc_stream

    conv_intr<
        CHANNELS,
        FILTERS,
        GROUPS,
        FILTERS_PER_GROUP,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t
    >(in,weights,window_stream,weight_stream);

    conv_mul<
        1,
        1,
        1,
        CHANNELS,
        FILTERS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        conv_acc_t
    >(window_stream,weight_stream,acc_stream);

    conv_acc<
        1,
        1,
        1,
        CHANNELS,
        FILTERS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_acc_t
    >(acc_stream, out);

}


/**
 *  conv T
 *  - single iteration
 *  - single filter
 */

template<
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t weights[DIVIDE(CHANNELS,GROUPS)][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

//#pragma HLS stable variable=weights


#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    printf("Conv version T, full conv, 1 iter, 1 fil\n");
    const unsigned int fine = FINE;

    stream_t(conv_data_t) window_stream[fine];
    stream_t(conv_weight_t) weight_stream[fine];
    stream_t(conv_acc_t) acc_stream[fine];

    #pragma HLS STREAM variable=window_stream
    #pragma HLS STREAM variable=weight_stream
    #pragma HLS STREAM variable=acc_stream

    conv_intr<
        CHANNELS,
        GROUPS,
        CHANNELS_PER_GROUP,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t
    >(in,weights,window_stream,weight_stream);

    conv_mul<
        1,
        1,
        1,
        CHANNELS,
        1,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        conv_acc_t
    >(window_stream,weight_stream,acc_stream);

    conv_acc<
        1,
        1,
        1,
        CHANNELS,
        1,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_acc_t
    >(acc_stream, out);

}

/**
 *  conv
 *  - single iteration
 *  - single filter
 *  - single channel per group
 */

template<
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int FINE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) in[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    const conv_weight_t weights[1][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    printf("Conv version U, 1 iter, 1 fil, 1 ch per grp\n");
    const unsigned int fine = FINE;

    stream_t(conv_data_t) window_stream[fine];
    stream_t(conv_weight_t) weight_stream[fine];
    stream_t(conv_acc_t) acc_stream[fine];

    #pragma HLS STREAM variable=window_stream
    #pragma HLS STREAM variable=weight_stream
    #pragma HLS STREAM variable=acc_stream

    conv_intr<
        CHANNELS,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t
    >(in,weights,window_stream,weight_stream);

    conv_mul<
        1,
        1,
        1,
        CHANNELS,
        1,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_data_t,
        conv_weight_t,
        conv_acc_t
    >(window_stream,weight_stream,acc_stream);

    conv_acc<
        1,
        1,
        1,
        CHANNELS,
        1,
        GROUPS,
        FINE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        conv_acc_t
    >(acc_stream, out);

}

/**
 *  point-wise convolution V
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FILTERS_PER_GROUP,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) &in,
    const conv_weight_t weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][1][1],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF

    printf("Conv version V, pointwise full conv\n");
    const unsigned batch_size   = BATCH_SIZE;
    const unsigned rows         = ROWS;
    const unsigned cols         = COLS;
    const unsigned channels     = CHANNELS;
    const unsigned filters      = FILTERS;
    const unsigned groups       = GROUPS;

    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

    //conv_data_t window_cache;
    //conv_acc_t acc;
    conv_data_t window_cache;
    conv_acc_t dot;
    pixel_loop: for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        unsigned int weight_index = 0;
        channel_loop: for(unsigned int channel_index=0;channel_index<channels_per_group;channel_index++) {
            filter_loop: for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
                #pragma HLS loop_flatten
                #pragma HLS PIPELINE II=1
                // #pragma HLS dependence variable=windowCache intra RAW true
                if(filter_index%filters_per_group == 0) {
                    //DO_PRAGMA(HLS occurence cycle=batch_size*rows*cols*channels)
                    window_cache = in.read();
                }
                // perform the dot product
                dot.data = window_cache.data * weights[weight_index][0][0];
                dot.batchid=window_cache.batchid;
                // write to the dotproduct to the output
                out.write(dot);
                // increment weights index
                weight_index++;
            }
        }
    }
}

/**
 *  point-wise convolution W
 *  - single filter
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) &in,
    const conv_weight_t weights[DIVIDE(CHANNELS,GROUPS)][1][1],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF

    printf("Conv version W, point wise\n");
    const unsigned batch_size   = BATCH_SIZE;
    const unsigned rows         = ROWS;
    const unsigned cols         = COLS;
    const unsigned channels     = CHANNELS;
    const unsigned groups       = GROUPS;

    const unsigned int channels_per_group = DIVIDE(channels,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

    // cache for the incoming sample
    conv_data_t window_cache;
    // result for the dot product
    conv_acc_t dot;

    pixel_loop: for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        unsigned int weight_index = 0;
        for(unsigned int channel_index=0;channel_index<channels_per_group;channel_index++) {
            #pragma HLS loop_flatten
            #pragma HLS PIPELINE II=1
            // update the cache
            window_cache = in.read();
            // perform the dot product
            dot.data = window_cache.data * weights[weight_index][0][0];
            dot.batchid=window_cache.batchid;
            // write to the dotproduct to the output
            out.write(dot);
            // increment weights index
            weight_index++;
        }
    }
}

/**
 *  point-wise convolution X
 *  - single channel
 */

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FILTERS_PER_GROUP,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) &in,
    const conv_weight_t weights[DIVIDE(FILTERS,GROUPS)][1][1],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF

    printf("Conv version X, pointwise\n");
    const unsigned batch_size   = BATCH_SIZE;
    const unsigned rows         = ROWS;
    const unsigned cols         = COLS;
    const unsigned channels     = CHANNELS;
    const unsigned filters      = FILTERS;
    const unsigned groups       = GROUPS;

    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

    // cache for the incoming sample
    conv_data_t window_cache;
    // result for the dot product
    conv_acc_t dot;

    pixel_loop: for(unsigned int pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        unsigned int weight_index = 0;
        for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
            #pragma HLS loop_flatten
            #pragma HLS PIPELINE II=1
            // update the cache
            if(filter_index%filters_per_group == 0) {
                window_cache = in.read();
            }
            // perform the dot product
            dot.data = window_cache.data * weights[weight_index][0][0];
            dot.batchid=window_cache.batchid;
            // write to the dotproduct to the output
            out.write(dot);
            // increment weights index
            weight_index++;
        }
    }
}

/**
 *  point-wise convolution Y
 *  - single iteration
 */

template<
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    unsigned int FILTERS_PER_GROUP,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) &in,
    const conv_weight_t weights[DIVIDE(CHANNELS*FILTERS,GROUPS)][1][1],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF

    printf("Conv version Y, pointwise\n");
    const unsigned channels     = CHANNELS;
    const unsigned filters      = FILTERS;
    const unsigned groups       = GROUPS;

    const unsigned int channels_per_group = DIVIDE(channels,groups);
    const unsigned int filters_per_group  = DIVIDE(filters ,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

    // cache for the incoming sample
    conv_data_t window_cache;
    // result for the dot product
    conv_acc_t dot;

    unsigned int weight_index = 0;
    for(unsigned int channel_index=0;channel_index<channels_per_group;channel_index++) {
        for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
            #pragma HLS loop_flatten
            #pragma HLS PIPELINE II=1
            // update the cache
            if(filter_index%filters_per_group == 0) {
                window_cache = in.read();
                //printf("C.Y in idx:"<<channel_index*filters+filter_index<<", ";
            }
            // perform the dot product
            dot.data = window_cache.data * weights[weight_index][0][0];
            dot.batchid=window_cache.batchid;
            // write to the dotproduct to the output
            out.write(dot);
            //printf("C.Y out idx:"<<channel_index*filters+filter_index);
            // increment weights index
            weight_index++;
        }
    }
}

/**
 *  point-wise convolution Z
 *  - single iteration
 *  - single filter
 */

template<
    unsigned int CHANNELS,
    unsigned int GROUPS,
    unsigned int CHANNELS_PER_GROUP,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) &in,
    const conv_weight_t weights[DIVIDE(CHANNELS,GROUPS)][1][1],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF

    printf("Conv version Z, pointwise\n");
    const unsigned channels     = CHANNELS;
    const unsigned groups       = GROUPS;

    const unsigned int channels_per_group = DIVIDE(channels,groups);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

    // cache for the incoming sample
    conv_data_t window_cache;
    // result for the dot product
    conv_acc_t dot;

    unsigned int weight_index = 0;
    for(unsigned int channel_index=0;channel_index<channels_per_group;channel_index++) {
        #pragma HLS PIPELINE II=1
        // update the cache
        window_cache = in.read();
        // perform the dot product
        dot.data = window_cache.data * weights[weight_index][0][0];
        dot.batchid=window_cache.batchid;
        // write to the dotproduct to the output
        out.write(dot);
        // increment weights index
        weight_index++;
    }
}

/**
 *  point-wise convolution AA
 *  - single iteration
 *  - single channel (per group)
 */

template<
    unsigned int CHANNELS,
    unsigned int FILTERS,
    unsigned int GROUPS,
    unsigned int FILTERS_PER_GROUP,
    typename conv_data_t,
    typename conv_weight_t,
    typename conv_acc_t
>
void conv(
    stream_t(conv_data_t) &in,
    const conv_weight_t weights[DIVIDE(FILTERS,GROUPS)][1][1],
    stream_t(conv_acc_t) &out
)
{

#pragma HLS INLINE OFF

    printf("Conv version AA, pointwise\n");
    const unsigned channels = CHANNELS;
    const unsigned filters  = FILTERS;

    const unsigned filters_per_group = DIVIDE(FILTERS,GROUPS);

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=out

    // cache for the incoming sample
    conv_data_t window_cache;
    // result for the dot product
    conv_acc_t dot;

    unsigned int weight_index = 0;
    for(unsigned int filter_index=0;filter_index<filters;filter_index++) {
        #pragma HLS PIPELINE II=1
         // update the cache
        if(filter_index%filters_per_group == 0) {
            window_cache = in.read();
        }
        // perform the dot product
        dot.data = window_cache.data * weights[weight_index][0][0];
        dot.batchid=window_cache.batchid;
        // write to the dotproduct to the output
        out.write(dot);
        // increment weights index
        weight_index++;
    }
}

#endif
