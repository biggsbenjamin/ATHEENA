#include "mem_read_tb.hpp"

#define MODULE_NAME MEM_READ
#define name        test
#include "mem_read.hpp"

void mem_read_top(
    volatile mem_int *in_hw_0,
    volatile mem_int *in_hw_1,
    volatile mem_int *in_hw_2,
    volatile mem_int *in_hw_3,
    hls::stream<data_t> in[MEM_READ_COARSE_IN]
)
{
    const int size_in = MEM_READ_BATCH_SIZE*MEM_READ_ROWS_IN*MEM_READ_COLS_IN*DIVIDE(MEM_READ_CHANNELS_IN,MEM_READ_COARSE_IN);
    DO_PRAGMA( HLS INTERFACE m_axi port=in_hw_0 depth=size_in num_read_outstanding=1 max_read_burst_length=256)
    DO_PRAGMA( HLS INTERFACE m_axi port=in_hw_1 depth=size_in num_read_outstanding=1 max_read_burst_length=256)
    DO_PRAGMA( HLS INTERFACE m_axi port=in_hw_2 depth=size_in num_read_outstanding=1 max_read_burst_length=256)
    DO_PRAGMA( HLS INTERFACE m_axi port=in_hw_3 depth=size_in num_read_outstanding=1 max_read_burst_length=256)
    #pragma HLS INTERFACE axis port=in

    #pragma HLS DATAFLOW
    test_mem_read<data_t>(in_hw_0,in_hw_1,in_hw_2,in_hw_3,in);
}

#undef MODULE_NAME
#undef name
