#include "mem_write_tb.hpp"

#define MODULE_NAME MEM_WRITE
#define name        test
#include "mem_write.hpp"

void mem_write_top(
    volatile mem_int *in_hw_0,
    volatile mem_int *in_hw_1,
    volatile mem_int *in_hw_2,
    volatile mem_int *in_hw_3,
    hls::stream<data_t> in[MEM_WRITE_COARSE_OUT]
)
{
    const int size_in = MEM_WRITE_BATCH_SIZE*MEM_WRITE_ROWS_OUT*MEM_WRITE_COLS_OUT*DIVIDE(MEM_WRITE_CHANNELS_OUT,MEM_WRITE_COARSE_OUT);
    DO_PRAGMA( HLS INTERFACE m_axi port=in_hw_0 depth=size_in num_write_outstanding=1 max_write_burst_length=256)
    DO_PRAGMA( HLS INTERFACE m_axi port=in_hw_1 depth=size_in num_write_outstanding=1 max_write_burst_length=256)
    DO_PRAGMA( HLS INTERFACE m_axi port=in_hw_2 depth=size_in num_write_outstanding=1 max_write_burst_length=256)
    DO_PRAGMA( HLS INTERFACE m_axi port=in_hw_3 depth=size_in num_write_outstanding=1 max_write_burst_length=256)
    #pragma HLS INTERFACE axis port=in

    #pragma HLS DATAFLOW
    test_mem_write<data_t>(in,in_hw_0,in_hw_1,in_hw_2,in_hw_3);
}

#undef MODULE_NAME
#undef name
