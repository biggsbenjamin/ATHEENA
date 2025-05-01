#include "common_tb.hpp"
#include "exponen_tb.hpp"

int main()
{

    int err = 0;
    std::string input_path  = std::string(DATA_DIR)+"/input.dat";
    std::string output_path = std::string(DATA_DIR)+"/output.dat";

    // in/out streams
    stream_t(exp_t) in;
    stream_t(exp_f_t) out;
    stream_t(exp_f_t) out_valid;
    //hls::stream<float> out;
    //hls::stream<float> out_valid;

    // test inputs data
    static exp_t test_in[EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_CHANNELS];
    static exp_f_t test_out[EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_CHANNELS];

    // load data_in
    load_data<
        EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_CHANNELS,
        exp_t
    >(input_path,test_in);

    // load data_out
    load_data<
        EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_CHANNELS,
        exp_f_t
    >(output_path,test_out);

    // convert input stream
    to_stream<
        EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_CHANNELS,
        exp_t
    >(test_in,in);

    // convert to out valid stream
    to_stream<
        EXPONEN_ROWS*EXPONEN_COLS*EXPONEN_CHANNELS,
        exp_f_t
    >(test_out,out_valid);

    // run exponen
    exponen_top(in,out);

    printf("\r\n\t EXPONEN #1\r\n");
    //err += checkStreamEqual <exp_t> (out,out_valid,false);
    err += checkStreamEqual <exp_f_t> (out,out_valid,false);
    
    return err;
}
