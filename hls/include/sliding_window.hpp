#ifndef SLIDING_WINDOW_HPP_
#define SLIDING_WINDOW_HPP_

#include "common.hpp"

/*template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PAD_TOP,
    unsigned int PAD_RIGHT,
    unsigned int PAD_BOTTOM,
    unsigned int PAD_LEFT,
    unsigned int KERNEL_SIZE,
    typename sliding_window_t
>
void sliding_window_line_shift_1d_horizontal(
    stream_t(sliding_window_t) &in,
    stream_t(sliding_window_t) frame_buffer[1][KERNEL_SIZE]
)
{

#pragma HLS INLINE OFF

    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int pad_top       = PAD_TOP;
    const unsigned int pad_right     = PAD_RIGHT;
    const unsigned int pad_bottom    = PAD_BOTTOM;
    const unsigned int pad_left      = PAD_LEFT;
    const unsigned int kernel_size   = KERNEL_SIZE;

    #pragma HLS STREAM variable=in
    #pragma HLS STREAM variable=frame_buffer
    #pragma HLS ARRAY_PARTITION variable=frame_buffer complete dim=0

    stream_t(sliding_window_t) window_buffer[kernel_size-1]; // pixel window cache
    DO_PRAGMA( HLS STREAM variable=window_buffer depth=channels+16 )
    #pragma HLS ARRAY_PARTITION variable=window_buffer complete dim=0
    #pragma HLS resource variable=window_buffer core=FIFO_BRAM

    sliding_window_t frame_cache[kernel_size];
    #pragma HLS ARRAY_PARTITION variable=frame_cache complete dim=0

    in_loop_batch: for(unsigned int batch_index=0;batch_index<batch_size;batch_index++) {
        in_loop_rows: for(unsigned int row_index=0;row_index<rows+pad_bottom+pad_top;row_index++) {
            in_loop_cols: for(unsigned int col_index=0;col_index<cols+pad_left+pad_right;col_index++) {
                in_loop_channels: for(unsigned int channel_index=0;channel_index<channels;channel_index++) {

                    #pragma HLS loop_flatten
                    #pragma HLS PIPELINE II=1 rewind
                    #pragma HLS DEPENDENCE variable=window_buffer   WAR intra true
                    #pragma HLS DEPENDENCE variable=frame_cache     WAR intra true
                    sliding_window_t pixel;

                    // read in pixel
                    if( row_index < pad_bottom ) {
                        pixel = 0;
                    }
                    else if ( row_index > rows+pad_bottom-1 ) {
                        pixel = 0;
                    }
                    else if ( col_index < pad_left ) {
                        pixel = 0;
                    }
                    else if (col_index > cols+pad_left-1 ) {
                        pixel = 0;
                    }
                    else {
                        pixel = in.read();
                    }

                    // fill top line of window buffer and line buffer
                    if ( (row_index == 0) && (col_index < kernel_size-1) ) {
                        window_buffer[col_index].write(pixel);
                        frame_cache[row_index][col_index] = pixel;
                    }

                    // main loop
                    else {

                        // read window buffer into window cache
                        for(unsigned char k2=0;k2<kernel_size-1;k2++) {
                            frame_cache[0][k2] = window_buffer[k2].read();
                        }

                        // read the top corner into window cache
                        frame_cache[0][kernel_size-1] = pixel;

                        // update window cache
                        if ( !( (row_index == rows+pad_top+pad_bottom-1) && (col_index == cols+pad_left+pad_right-1) ) ) {
                            for(unsigned char k2=0;k2<kernel_size-1;k2++) {
                                window_buffer[k2].write(frame_cache[0][k2+1]);
                            }
                        }

                        // send window cache to frame buffer
                        for(unsigned char k2=0;k2<kernel_size;k2++) {
                            frame_buffer[0][k2].write(frame_cache[0][k2]);
                        }
                    }
                }
            }
        }
    }
}

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PAD_TOP,
    unsigned int PAD_RIGHT,
    unsigned int PAD_BOTTOM,
    unsigned int PAD_LEFT,
    unsigned int KERNEL_SIZE,
    typename sliding_window_t
>
void sliding_window_line_shift_1d_vertical(
    stream_t(sliding_window_t) &in,
    stream_t(sliding_window_t) frame_buffer[KERNEL_SIZE][1]
)
{

#pragma HLS INLINE OFF

    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int pad_top       = PAD_TOP;
    const unsigned int pad_right     = PAD_RIGHT;
    const unsigned int pad_bottom    = PAD_BOTTOM;
    const unsigned int pad_left      = PAD_LEFT;
    const unsigned int kernel_size   = KERNEL_SIZE;

    #pragma HLS STREAM variable=in
    #pragma HLS STREAM variable=frame_buffer
    #pragma HLS ARRAY_PARTITION variable=frame_buffer complete dim=0

    stream_t(sliding_window_t) line_buffer[kernel_size-1];
    DO_PRAGMA( HLS STREAM variable=line_buffer depth=cols*channels+pad_left*channels+pad_right*channels+16 )
    #pragma HLS ARRAY_PARTITION variable=line_buffer complete dim=0
    #pragma HLS resource variable=line_buffer core=FIFO_BRAM

    sliding_window_t frame_cache[kernel_size][1];
    #pragma HLS ARRAY_PARTITION variable=frame_cache complete dim=0

    in_loop_batch: for(unsigned int batch_index=0;batch_index<batch_size;batch_index++) {
        in_loop_rows: for(unsigned int row_index=0;row_index<rows+pad_bottom+pad_top;row_index++) {
            in_loop_cols: for(unsigned int col_index=0;col_index<cols+pad_left+pad_right;col_index++) {
                in_loop_channels: for(unsigned int channel_index=0;channel_index<channels;channel_index++) {

                    #pragma HLS loop_flatten
                    #pragma HLS PIPELINE II=1 rewind
                    #pragma HLS DEPENDENCE variable=line_buffer     WAR intra true
                    #pragma HLS DEPENDENCE variable=frame_cache     WAR intra true
                    sliding_window_t pixel;

                    // read in pixel
                    if( row_index < pad_bottom ) {
                        pixel = 0;
                    }
                    else if ( row_index > rows+pad_bottom-1 ) {
                        pixel = 0;
                    }
                    else if ( col_index < pad_left ) {
                        pixel = 0;
                    }
                    else if (col_index > cols+pad_left-1 ) {
                        pixel = 0;
                    }
                    else {
                        pixel = in.read();
                    }

                    // init first part of window cache
                    if ( (row_index < kernel_size-1) ) {
                        line_buffer[row_index].write(pixel);
                    }

                    // main loop
                    else {
                        // read out line buffer to window cache
                        for(unsigned char k1=0;k1<kernel_size-1;k1++) {
                            frame_cache[k1][0] = line_buffer[k1].read();
                        }

                        // read the top corner into window cache
                        frame_cache[kernel_size-1][0] = pixel;

                        // update the line buffer
                        if ( !(row_index == rows+pad_top+pad_bottom-1) ) {
                            for(unsigned char k1=0;k1<kernel_size-1;k1++) {
                                line_buffer[k1].write(frame_cache[k1+1][0]);
                            }
                        }
                        // send window cache to frame buffer
                        for(unsigned char k1=0;k1<kernel_size;k1++) {
                            frame_buffer[k1][0].write(frame_cache[k1][0]);
                        }
                    }
                }
            }
        }
    }
}*/

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PAD_TOP,
    unsigned int PAD_RIGHT,
    unsigned int PAD_BOTTOM,
    unsigned int PAD_LEFT,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename sliding_window_t
>
void sliding_window_line_shift(
    stream_t(sliding_window_t) &in,
    stream_t(sliding_window_t) frame_buffer[KERNEL_SIZE_X][KERNEL_SIZE_Y]
)
{

#pragma HLS INLINE OFF

    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int pad_top       = PAD_TOP;
    const unsigned int pad_right     = PAD_RIGHT;
    const unsigned int pad_bottom    = PAD_BOTTOM;
    const unsigned int pad_left      = PAD_LEFT;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;

    #pragma HLS STREAM variable=in
    #pragma HLS STREAM variable=frame_buffer
    #pragma HLS ARRAY_PARTITION variable=frame_buffer complete dim=0

    stream_t(sliding_window_t) line_buffer[kernel_size_x-1];
    DO_PRAGMA( HLS STREAM variable=line_buffer depth=cols*channels+pad_left*channels+pad_right*channels+16 )
    #pragma HLS ARRAY_PARTITION variable=line_buffer complete dim=0
    #pragma HLS resource variable=line_buffer core=FIFO_BRAM

    stream_t(sliding_window_t) window_buffer[kernel_size_x][kernel_size_y-1]; // pixel window cache
    DO_PRAGMA( HLS STREAM variable=window_buffer depth=channels+16 )
    #pragma HLS ARRAY_PARTITION variable=window_buffer complete dim=0
    //#pragma HLS resource variable=window_buffer core=FIFO_BRAM

    sliding_window_t frame_cache[kernel_size_x][kernel_size_y];
    #pragma HLS ARRAY_PARTITION variable=frame_cache complete dim=0

    in_loop_batch: for(unsigned int batch_index=0;batch_index<batch_size;batch_index++) {
        in_loop_rows: for(unsigned int row_index=0;row_index<rows+pad_bottom+pad_top;row_index++) {
            in_loop_cols: for(unsigned int col_index=0;col_index<cols+pad_left+pad_right;col_index++) {
                in_loop_channels: for(unsigned int channel_index=0;channel_index<channels;channel_index++) {
                    #pragma HLS loop_flatten
                    #pragma HLS PIPELINE II=1 rewind
                    #pragma HLS DEPENDENCE variable=line_buffer     WAR intra true
                    #pragma HLS DEPENDENCE variable=window_buffer   WAR intra true
                    #pragma HLS DEPENDENCE variable=frame_cache     WAR intra true
                    sliding_window_t pixel;

                    // read in pixel
                    if( row_index < pad_bottom ) {
                        pixel = 0;
                    }
                    else if ( row_index > rows+pad_bottom-1 ) {
                        pixel = 0;
                    }
                    else if ( col_index < pad_left ) {
                        pixel = 0;
                    }
                    else if (col_index > cols+pad_left-1 ) {
                        pixel = 0;
                    }
                    else {
                        pixel = in.read();
                    }

                    // init first part of window cache
                    if ( (row_index < kernel_size_x-1) ) {
                        // fill window cache
                        if( col_index < kernel_size_y-1 ) {
                            window_buffer[row_index][col_index].write(pixel);
                            frame_cache[row_index][col_index] = pixel;
                            if ( row_index > 0 ) {
                                line_buffer[row_index-1].write(pixel);
                            }
                        }
                        else {
                            line_buffer[row_index].write(pixel);
                        }
                    }

                    // fill top line of window buffer and line buffer
                    else if ( (row_index == (kernel_size_x-1)) && (col_index < kernel_size_y-1) ) {
                        window_buffer[row_index][col_index].write(pixel);
                        frame_cache[row_index][col_index] = pixel;
                        line_buffer[kernel_size_x-2].write(pixel);
                    }

                    // main loop
                    else {

                        // read window buffer into window cache
                        for(unsigned char k1=0;k1<kernel_size_x;k1++) {
                            for(unsigned char k2=0;k2<kernel_size_y-1;k2++) {
                                frame_cache[k1][k2] = window_buffer[k1][k2].read();
                            }
                        }

                        // read out line buffer to window cache
                        for(unsigned char k1=0;k1<kernel_size_x-1;k1++) {
                            frame_cache[k1][kernel_size_y-1] = line_buffer[k1].read();
                        }

                        // read the top corner into window cache
                        frame_cache[kernel_size_x-1][kernel_size_y-1] = pixel;

                        // update window buffer
                        if ( !( (row_index == rows+pad_top+pad_bottom-1) && (col_index == cols+pad_left+pad_right-1) ) ) {
                            for(unsigned char k1=0;k1<kernel_size_x;k1++) {
                                for(unsigned char k2=0;k2<kernel_size_y-1;k2++) {
                                    window_buffer[k1][k2].write(frame_cache[k1][k2+1]);
                                }
                            }
                        }
                        // update the line buffer
                        if ( !(row_index == rows+pad_top+pad_bottom-1) ) {
                            for(unsigned char k1=0;k1<kernel_size_x-1;k1++) {
                                line_buffer[k1].write(frame_cache[k1+1][kernel_size_y-1]);
                            }
                        }
                        // send window cache to frame buffer
                        for(unsigned char k1=0;k1<kernel_size_x;k1++) {
                            for(unsigned char k2=0;k2<kernel_size_y;k2++) {
                                frame_buffer[k1][k2].write(frame_cache[k1][k2]);
                            }
                        }
                    }
                }
            }
        }
    }
}

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PAD_TOP,
    unsigned int PAD_RIGHT,
    unsigned int PAD_BOTTOM,
    unsigned int PAD_LEFT,
    unsigned int ROW_STRIDE,
    unsigned int COL_STRIDE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename sliding_window_t,
    typename sw_external_t
>
void sliding_window_out(
    stream_t(sliding_window_t) frame_buffer[KERNEL_SIZE_X][KERNEL_SIZE_Y],
    //stream_t(sliding_window_t) out[KERNEL_SIZE_X][KERNEL_SIZE_Y]
    stream_t(batch_t) &id_in,
    stream_t(sw_external_t) out[KERNEL_SIZE_X][KERNEL_SIZE_Y]
)
{

#pragma HLS INLINE OFF

    #pragma HLS STREAM variable=frame_buffer
    #pragma HLS ARRAY_PARTITION variable=frame_buffer complete dim=0

    #pragma HLS STREAM variable=out
    #pragma HLS ARRAY_PARTITION variable=out complete dim=0

    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int pad_top       = PAD_TOP;
    const unsigned int pad_right     = PAD_RIGHT;
    const unsigned int pad_bottom    = PAD_BOTTOM;
    const unsigned int pad_left      = PAD_LEFT;
    const unsigned int row_stride    = ROW_STRIDE;
    const unsigned int col_stride    = COL_STRIDE;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;
    
    sw_external_t tmp;

    // writing frames out
    out_loop_batch: for(unsigned int batch_index=0;batch_index<batch_size;batch_index++) {
        out_loop_rows: for(unsigned int row_index=0;row_index<rows+pad_bottom+pad_top;row_index++) {
            out_loop_cols: for(unsigned int col_index=0;col_index<cols+pad_left+pad_right;col_index++) {
                out_loop_channels: for(unsigned int channel_index=0;channel_index<channels;channel_index++) {
                    tmp.batchid = id_in.read();
                    #pragma HLS loop_flatten
                    #pragma HLS PIPELINE II=1 rewind
                    if ( !( (row_index < (kernel_size_x-1)) || ( (row_index == (kernel_size_x-1)) && (col_index < kernel_size_y-1) ) ) ) {
                        for(unsigned char k1=0;k1<kernel_size_x;k1++) {
                            for(unsigned char k2=0;k2<kernel_size_y;k2++) {
                                tmp.data = frame_buffer[k1][k2].read();
                                if (
                                        (row_index >= (kernel_size_x-1)) &&
                                        ((row_index-kernel_size_x+1)%row_stride == 0) &&
                                        (col_index >= (kernel_size_y-1)) &&
                                        ((col_index-kernel_size_y+1)%col_stride == 0)
                                    ) {
                                        out[k1][k2].write(tmp);
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

/*template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PAD_TOP,
    unsigned int PAD_RIGHT,
    unsigned int PAD_BOTTOM,
    unsigned int PAD_LEFT,
    unsigned int ROW_STRIDE,
    unsigned int COL_STRIDE,
    unsigned int KERNEL_SIZE,
    typename sliding_window_t
>
void sliding_window_1d_horizontal(
    stream_t(sliding_window_t) &in,
    stream_t(sliding_window_t) out[1][KERNEL_SIZE]
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

    #pragma HLS STREAM variable=in
    #pragma HLS STREAM variable=out
    #pragma HLS ARRAY_PARTITION variable=out complete dim=0

    const unsigned int kernel_size = KERNEL_SIZE;

    stream_t(sliding_window_t) frame_buffer[1][kernel_size];
    #pragma HLS STREAM variable=frame_buffer
    #pragma HLS ARRAY_PARTITION variable=frame_buffer complete dim=0

    sliding_window_line_shift_1d_horizontal<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        PAD_TOP,
        PAD_RIGHT,
        PAD_BOTTOM,
        PAD_LEFT,
        KERNEL_SIZE,
        sliding_window_t
    >(in,frame_buffer);

    sliding_window_out<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        PAD_TOP,
        PAD_RIGHT,
        PAD_BOTTOM,
        PAD_LEFT,
        ROW_STRIDE,
        COL_STRIDE,
        1,
        KERNEL_SIZE,
        sliding_window_t
    >(frame_buffer,out);

}

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PAD_TOP,
    unsigned int PAD_RIGHT,
    unsigned int PAD_BOTTOM,
    unsigned int PAD_LEFT,
    unsigned int ROW_STRIDE,
    unsigned int COL_STRIDE,
    unsigned int KERNEL_SIZE,
    typename sliding_window_t
>
void sliding_window_1d_vertical(
    stream_t(sliding_window_t) &in,
    stream_t(sliding_window_t) out[KERNEL_SIZE][1]
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

    #pragma HLS STREAM variable=in
    #pragma HLS STREAM variable=out
    #pragma HLS ARRAY_PARTITION variable=out complete dim=0

    const unsigned int kernel_size = KERNEL_SIZE;

    stream_t(sliding_window_t) frame_buffer[kernel_size][1];
    #pragma HLS STREAM variable=frame_buffer
    #pragma HLS ARRAY_PARTITION variable=frame_buffer complete dim=0

    sliding_window_line_shift_1d_vertical<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        PAD_TOP,
        PAD_RIGHT,
        PAD_BOTTOM,
        PAD_LEFT,
        KERNEL_SIZE,
        sliding_window_t
    >(in,frame_buffer);

    sliding_window_out<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        PAD_TOP,
        PAD_RIGHT,
        PAD_BOTTOM,
        PAD_LEFT,
        ROW_STRIDE,
        COL_STRIDE,
        KERNEL_SIZE,
        1,
        sliding_window_t
    >(frame_buffer,out);

}*/

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PAD_TOP,
    unsigned int PAD_RIGHT,
    unsigned int PAD_BOTTOM,
    unsigned int PAD_LEFT,
    unsigned int ROW_STRIDE,
    unsigned int COL_STRIDE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename sliding_window_t,
    typename sw_external_t
>
void batch_splitter(
    stream_t(sw_external_t) &in,
    stream_t(sliding_window_t) &out,
    stream_t(batch_t) &batchid
)
{

#pragma HLS INLINE OFF

    const unsigned int batch_size    = BATCH_SIZE;
    const unsigned int rows          = ROWS;
    const unsigned int cols          = COLS;
    const unsigned int channels      = CHANNELS;
    const unsigned int pad_top       = PAD_TOP;
    const unsigned int pad_right     = PAD_RIGHT;
    const unsigned int pad_bottom    = PAD_BOTTOM;
    const unsigned int pad_left      = PAD_LEFT;
    const unsigned int kernel_size_x = KERNEL_SIZE_X;
    const unsigned int kernel_size_y = KERNEL_SIZE_Y;

    const unsigned int padded_row_size = rows+pad_bottom+pad_top;
    const unsigned int padded_col_size = cols+pad_left+pad_right;
    const unsigned int loop_lim = padded_row_size*padded_col_size*channels;
    const unsigned int input_size = rows*cols*channels; 
    #pragma HLS STREAM variable=in
    #pragma HLS STREAM variable=out
    #pragma HLS STREAM variable=batchid
    // from common.hpp
    sw_external_t b_data;
    batch_t id_s;

    in_loop_batch: for(unsigned int batch_index=0;batch_index<batch_size;batch_index++) {
        in_loop_rcc: for(unsigned int idx=0;idx<loop_lim;idx++) {
            #pragma HLS loop_flatten
            #pragma HLS PIPELINE II=1 rewind
            if (idx < input_size) {
                b_data = in.read();
                id_s = b_data.batchid;
                out.write(b_data.data);
            }

            batchid.write(id_s);
        }
    }
}

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PAD_TOP,
    unsigned int PAD_RIGHT,
    unsigned int PAD_BOTTOM,
    unsigned int PAD_LEFT,
    unsigned int ROW_STRIDE,
    unsigned int COL_STRIDE,
    unsigned int KERNEL_SIZE_X,
    unsigned int KERNEL_SIZE_Y,
    typename sliding_window_t,
    typename sw_external_t
>
void sliding_window(
    stream_t(sw_external_t) &in,
    //stream_t(sliding_window_t) &in,
    //stream_t(sliding_window_t) out[KERNEL_SIZE_X][KERNEL_SIZE_Y]
    stream_t(sw_external_t) out[KERNEL_SIZE_X][KERNEL_SIZE_Y]
)
{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

    #pragma HLS STREAM variable=in
    #pragma HLS STREAM variable=out
    #pragma HLS ARRAY_PARTITION variable=out complete dim=0
    
    //const unsigned int batch_size       = BATCH_SIZE;
    const unsigned int rows             = ROWS;
    const unsigned int cols             = COLS;
    const unsigned int channels         = CHANNELS;
    const unsigned int pad_top          = PAD_TOP;
    const unsigned int pad_right        = PAD_RIGHT;
    const unsigned int pad_bottom       = PAD_BOTTOM;
    const unsigned int pad_left         = PAD_LEFT;
    const unsigned int kernel_size_x    = KERNEL_SIZE_X;
    const unsigned int kernel_size_y    = KERNEL_SIZE_Y;

    const unsigned int padded_row_size = rows+pad_bottom+pad_top;
    const unsigned int padded_col_size = cols+pad_left+pad_right;
    const unsigned int loop_lim = padded_row_size*padded_col_size*channels;
    const unsigned int input_size = rows*cols*channels; 

    stream_t(sliding_window_t) data_buffer;
    DO_PRAGMA( HLS STREAM variable=data_buffer depth=loop_lim-input_size+8 )
    
    stream_t(batch_t) id_s;
    DO_PRAGMA( HLS STREAM variable=id_s depth=loop_lim-input_size+8 )

    stream_t(sliding_window_t) frame_buffer[kernel_size_x][kernel_size_y];
    //DO_PRAGMA( pragma HLS STREAM variable=frame_buffer depth=kernel_size_x*kernel_size_y+8 )
    #pragma HLS STREAM variable=frame_buffer
    #pragma HLS ARRAY_PARTITION variable=frame_buffer complete dim=0


    batch_splitter<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        PAD_TOP,
        PAD_RIGHT,
        PAD_BOTTOM,
        PAD_LEFT,
        ROW_STRIDE,
        COL_STRIDE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        sliding_window_t,
        sw_external_t
    >(in,data_buffer,id_s);

    sliding_window_line_shift<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        PAD_TOP,
        PAD_RIGHT,
        PAD_BOTTOM,
        PAD_LEFT,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        sliding_window_t
    >(data_buffer,frame_buffer);

    sliding_window_out<
        BATCH_SIZE,
        ROWS,
        COLS,
        CHANNELS,
        PAD_TOP,
        PAD_RIGHT,
        PAD_BOTTOM,
        PAD_LEFT,
        ROW_STRIDE,
        COL_STRIDE,
        KERNEL_SIZE_X,
        KERNEL_SIZE_Y,
        sliding_window_t,
        sw_external_t
    >(frame_buffer,id_s,out);
}

#endif
