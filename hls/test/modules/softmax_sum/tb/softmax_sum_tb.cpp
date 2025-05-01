#include "common_tb.hpp"
#include "softmax_sum_tb.hpp"

int main()
{

    int err = 0;
    std::string input_path  = std::string(DATA_DIR)+"/input.dat";
    std::string output_path = std::string(DATA_DIR)+"/output.dat";

    // in/out streams
    stream_t(sfmsm_t) in;
    stream_t(sfmsm_t) out;
    stream_t(sfmsm_t) out_valid;
    //hls::stream<float> in;
    //hls::stream<float> out;
    //hls::stream<float> out_valid;

    // test inputs data
    static sfmsm_t test_in[SOFTMAX_SUM_BATCH_SIZE*SOFTMAX_SUM_ROWS*SOFTMAX_SUM_COLS*SOFTMAX_SUM_CHANNELS];
    static sfmsm_t test_out[SOFTMAX_SUM_BATCH_SIZE];
    //static float test_in[SOFTMAX_SUM_BATCH_SIZE*SOFTMAX_SUM_ROWS*SOFTMAX_SUM_COLS*SOFTMAX_SUM_CHANNELS];
    //static float test_out[SOFTMAX_SUM_BATCH_SIZE];

    // load data_in
    load_data_buff<
        SOFTMAX_SUM_BATCH_SIZE,           
        SOFTMAX_SUM_ROWS*SOFTMAX_SUM_COLS*SOFTMAX_SUM_CHANNELS,
        sfmsm_t
        //float
    >(input_path,test_in);

    // load data_out
    load_data_buff<
        SOFTMAX_SUM_BATCH_SIZE,
        1,
        sfmsm_t
        //float
    >(output_path,test_out);

    // convert input stream
    to_stream<
        SOFTMAX_SUM_BATCH_SIZE*SOFTMAX_SUM_ROWS*SOFTMAX_SUM_COLS*SOFTMAX_SUM_CHANNELS,
        sfmsm_t
        //float
    >(test_in,in);

    // convert to out valid stream
    to_stream<
        SOFTMAX_SUM_BATCH_SIZE,
        sfmsm_t
        //float
    >(test_out,out_valid);

    // run softmax_sum
    softmax_sum_top(in,out);

    printf("\r\n\t SOFTMAX_SUM #1\r\n");
    err += checkStreamEqual <sfmsm_t> (out,out_valid,false);
    //err += checkStreamEqual <float> (out,out_valid,true);
    
    return err;
}
