#ifndef MEM_READ_HPP_
#define MEM_READ_HPP_

#include "common.hpp"

template<
    unsigned int BATCH_SIZE,
    unsigned int ROWS,
    unsigned int COLS,
    unsigned int CHANNELS,
    unsigned int PORTS,
    unsigned int STREAMS,
    typename type_t
>
void mem_read(
    volatile mem_int in_hw[PORTS][BATCH_SIZE*ROWS*COLS*DIVIDE(CHANNELS,STREAMS)],
    stream_t(type_t) in[STREAMS]
)
{

#pragma HLS INLINE OFF

    const unsigned batch_size           = BATCH_SIZE;
    const unsigned rows                 = ROWS;
    const unsigned cols                 = COLS;
    const unsigned channels             = CHANNELS;
    const unsigned ports                = PORTS;
    const unsigned streams              = STREAMS;
    const unsigned channels_per_stream  = DIVIDE(channels,streams);
    const unsigned dma_channels         = DIVIDE(DMA_WIDTH,DATA_WIDTH);

#pragma HLS STREAM variable=in depth=256
#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    read_loop: for (unsigned long size_index=0; size_index < batch_size*rows*cols*channels_per_stream; size_index++) {
        #pragma HLS PIPELINE II=1

        mem_int port_cache[ports];
        #pragma HLS ARRAY_PARTITION variable=port_cache complete dim=0

        port_read_loop: for (unsigned port_index=0; port_index < ports; port_index++) {
            port_cache[port_index] = in_hw[port_index][size_index];
        }

        stream_loop: for (unsigned int stream_index=0; stream_index < streams; stream_index++) {

            // get the port index
            unsigned int port_index = (int)(stream_index/dma_channels);

            // get the stream value
            type_t stream_cache = 0;
            stream_cache.range() = ( ( ( port_cache[port_index] ) >> ( ( stream_index%dma_channels ) * DATA_WIDTH ) ) & BIT_MASK );

            /* printf("%d: %f\n", port_cache[port_index], stream_cache.to_float()); */

            // write to the stream
            in[stream_index].write(stream_cache);

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
    bool EE_MODE,
    typename type_t
>
void mem_read(
    volatile mem_int in_hw[PORTS][BATCH_SIZE*ROWS*COLS*DIVIDE(CHANNELS,STREAMS)],
    stream_t(uint16_t) &batch,
    stream_t(type_t) in[STREAMS]
)
{

#pragma HLS INLINE OFF

    const unsigned batch_size           = BATCH_SIZE;
    const unsigned rows                 = ROWS;
    const unsigned cols                 = COLS;
    const unsigned channels             = CHANNELS;
    const unsigned ports                = PORTS;
    const unsigned streams              = STREAMS;
    const unsigned channels_per_stream  = DIVIDE(channels,streams);
    const unsigned dma_channels         = DIVIDE(DMA_WIDTH,DATA_WIDTH);

#pragma HLS STREAM variable=in depth=256
#pragma HLS STREAM variable=batch 
#pragma HLS ARRAY_PARTITION variable=in complete dim=0

    uint16_t batch_id;

    batch_loop: for (unsigned long b_index=0; b_index < batch_size; b_index++) {
        read_loop: for (unsigned long size_index=0; size_index < rows*cols*channels_per_stream; size_index++) {
            #pragma HLS PIPELINE II=1

            mem_int port_cache[ports];
#pragma HLS ARRAY_PARTITION variable=port_cache complete dim=0

            port_read_loop: for (unsigned port_index=0; port_index < ports; port_index++) {
                //if ( streams_in > port_index*dma_channels ) {
                    if(size_index == 0 && port_index == 0) { //should execute once per input sample
                        batch_id = uint16_t{ in_hw[port_index][size_index] }; //unlikely to work
                        batch.write(batch_id);
                    }
                    port_cache[port_index] = in_hw[port_index][size_index+1];

                    // mem_int tmp = in_hw[port_index][size_index];
                //}
            }
            stream_loop: for (unsigned int stream_index=0; stream_index < streams; stream_index++) {

                //
                unsigned int port_index = (int)(stream_index/dma_channels);

                //
                type_t stream_cache = 0;
                stream_cache.range() = ( ( ( port_cache[port_index] ) >> ( ( stream_index%dma_channels ) * DATA_WIDTH ) ) & BIT_MASK );
                // write to the stream
                in[stream_index].write(stream_cache);
            }
        }
    }
}
*/
#endif
