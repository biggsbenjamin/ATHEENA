#ifndef MEM_WRITE_HPP_
#define MEM_WRITE_HPP_

#include "common.hpp"

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PORTS,
    unsigned int STREAMS,
    unsigned int WEIGHTS_RELOADING_FACTOR,
    typename type_t
>
void mem_write(
    int weights_reloading_index,
    stream_t(type_t) out[STREAMS],
    volatile mem_int out_hw[PORTS][BATCH_SIZE*ROWS*COLS*DIVIDE(CHANNELS,STREAMS)*WEIGHTS_RELOADING_FACTOR]
)
{

#pragma HLS INLINE OFF

    const unsigned batch_size               = BATCH_SIZE;
    const unsigned rows                     = ROWS;
    const unsigned cols                     = COLS;
    const unsigned channels                 = CHANNELS;
    const unsigned ports                    = PORTS;
    const unsigned streams                  = STREAMS;
    const unsigned weights_reloading_factor = WEIGHTS_RELOADING_FACTOR;
    const unsigned channels_per_stream      = DIVIDE(channels,streams);
    const unsigned dma_channels             = DIVIDE(DMA_WIDTH,DATA_WIDTH);

#pragma HLS STREAM variable=out depth=256
#pragma HLS ARRAY_PARTITION variable=out complete dim=0

    pixel_loop: for(unsigned pixel_index=0;pixel_index<batch_size*rows*cols;pixel_index++) {
        channel_loop: for(unsigned channel_index=0;channel_index<channels_per_stream;channel_index++) {
            #pragma HLS PIPELINE II=1
            mem_int port_cache[ports] = {0};
            #pragma HLS dependence variable=port_cache intra RAW true
            streams_loop: for(unsigned stream_index=0; stream_index<streams; stream_index++) {
                type_t stream_cache = out[stream_index].read();
                unsigned int port_index = (int) (stream_index/dma_channels);
                port_cache[port_index] |= ( ( stream_cache.range() & BIT_MASK ) << ( ( stream_index%dma_channels ) * DATA_WIDTH ) );
            }
            port_write_loop: for (unsigned port_index=0; port_index < ports; port_index++) {
                int out_index = pixel_index*channels_per_stream*weights_reloading_factor+weights_reloading_index*channels_per_stream+channel_index;
                out_hw[port_index][out_index] = port_cache[port_index];
            }
        }
    }
}

/*template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PORTS,
    unsigned int STREAMS,
    unsigned int WEIGHTS_RELOADING_FACTOR,
    bool EE_MODE,
    typename type_t
>
void mem_write(
    int weights_reloading_index,
    stream_t(type_t) out[STREAMS],
    stream_t(uint16_t) &batch,
    volatile mem_int out_hw[PORTS][BATCH_SIZE*((ROWS*COLS*DIVIDE(CHANNELS,STREAMS)*WEIGHTS_RELOADING_FACTOR)+1)]
)
{

#pragma HLS INLINE OFF
#pragma HLS INTERFACE ap_ctrl_chain port=return

    const unsigned batch_size               = BATCH_SIZE;
    const unsigned rows                     = ROWS;
    const unsigned cols                     = COLS;
    const unsigned channels                 = CHANNELS;
    const unsigned ports                    = PORTS;
    const unsigned streams                  = STREAMS;
    const unsigned weights_reloading_factor = WEIGHTS_RELOADING_FACTOR;
    const unsigned channels_per_stream      = DIVIDE(channels,streams);
    const unsigned dma_channels             = DIVIDE(DMA_WIDTH,DATA_WIDTH);

#pragma HLS STREAM variable=out depth=256
#pragma HLS STREAM variable=batch 
#pragma HLS ARRAY_PARTITION variable=out complete dim=0
    uint16_t batch_id;
    //for EEmode I'm assuming 16bit output

    batch_loop: for (unsigned int batch_index=0;batch_index<batch_size;batch_index++) {
        batch_id = batch.read();
        pixel_loop: for(unsigned pixel_index=0;pixel_index<rows*cols;pixel_index++) {
            channel_loop: for(unsigned channel_index=0;channel_index<channels_per_stream;channel_index++) {
                #pragma HLS PIPELINE II=1
                mem_int port_cache[ports] = {0};
                #pragma HLS dependence variable=port_cache intra RAW true
                streams_loop: for(unsigned stream_index=0; stream_index<streams; stream_index++) {
                    type_t stream_cache = out[stream_index].read();
                    unsigned int port_index = (int) (stream_index/dma_channels);
                    port_cache[port_index] |= ( ( stream_cache.range() & BIT_MASK ) << ( ( stream_index%dma_channels ) * DATA_WIDTH ) );
                }
                port_write_loop: for (unsigned port_index=0; port_index < ports; port_index++) {
                    int out_index = (batch_index*rows*cols+1) + 
                                    pixel_index*channels_per_stream*weights_reloading_factor+
                                    weights_reloading_index*channels_per_stream+
                                    channel_index;
                    
                    if ((pixel_index==0) && (channel_index==0 ) && (port_index==0)) {
                        //should execute ONCE per batch index
                        //DO_PRAGMA(HLS occurrence cycle=rows*cols*channels_per_stream*ports*weights_reloading_factor)
                        int id_out_index =  batch_index*rows*cols + 
                                            pixel_index*channels_per_stream*weights_reloading_factor + 
                                            weights_reloading_index*channels_per_stream + 
                                            channel_index;
                        out_hw[port_index][id_out_index] = mem_int{batch_id}; //unlikely that this works
                    }
                    
                    out_hw[port_index][out_index] = port_cache[port_index];
                }
            }
        }
    }
}
*/
#endif
