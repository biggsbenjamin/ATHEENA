#include "common_tb.hpp"
#include "compare_tb.hpp"

int main()
{

    int err = 0;
    std::string input_path_max  = std::string(DATA_DIR)+"/input_max.dat";
    std::string input_path_thr  = std::string(DATA_DIR)+"/input_thr_mul.dat";
    std::string path_thr_val  = std::string(DATA_DIR)+"/thr_val.dat";
    std::string output_path = std::string(DATA_DIR)+"/output.dat";

    // in/out streams
    //hls::stream<float> max_in;
    //hls::stream<float> thr_in;
    stream_t(cmp_t) max_in;
    stream_t(cmp_t) thr_in;
    stream_t(ctrl_t) out;
    stream_t(ctrl_t) out_valid;

    //threshold value
    float thr_val[1] = { COMPARE_THR_VAL };
    // test inputs data
    static cmp_t test_max_in[COMPARE_BATCH_SIZE];
    static cmp_t test_thr_in[COMPARE_BATCH_SIZE];
    static ctrl_t test_out[COMPARE_BATCH_SIZE];

    //load threshold
    //load_data<
    //    float
    //>(path_thr_val, thr_val);

    // load data_in
    load_data_buff<
        COMPARE_BATCH_SIZE,
        1,
        cmp_t
    >(input_path_max,test_max_in);

    load_data_buff<
        COMPARE_BATCH_SIZE,
        1,
        cmp_t
    >(input_path_thr,test_thr_in);

    // load data_out
    load_data_buff<
        COMPARE_BATCH_SIZE,
        1,
        ctrl_t
    >(output_path,test_out);

    // convert input stream
    to_stream<
        COMPARE_BATCH_SIZE,
        cmp_t
    >(test_max_in,max_in);
    to_stream<
        COMPARE_BATCH_SIZE,
        cmp_t
    >(test_thr_in,thr_in);

    // convert to out valid stream
    to_stream<
        COMPARE_BATCH_SIZE,
        ctrl_t
    >(test_out,out_valid);

    // run compare
    compare_top(max_in, thr_in, thr_val, out);

    printf("\r\n\t COMPARE #1\r\n");
    err += checkStreamEqual <ctrl_t> (out,out_valid,false);
    //err += checkStreamEqual <float> (out,out_valid,true);
    
    return err;
}
