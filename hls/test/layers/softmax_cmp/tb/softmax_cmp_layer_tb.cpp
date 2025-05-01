#include "common_tb.hpp"
#include "softmax_cmp_layer_tb.hpp"

int main()
{
    int err = 0;

    std::string input_path  = std::string(DATA_DIR)+"/input.dat";
    std::string output_path = std::string(DATA_DIR)+"/output.dat";

    stream_t(softmax_cmp_layer_data_t) in[1];
    stream_t(softmax_cmp_layer_ctrl_t) out[SOFTMAX_CMP_LAYER_CTRL];
    stream_t(softmax_cmp_layer_ctrl_t) out_correct[SOFTMAX_CMP_LAYER_CTRL];

    const unsigned int fm_size = SOFTMAX_CMP_LAYER_ROWS*SOFTMAX_CMP_LAYER_COLS*SOFTMAX_CMP_LAYER_CHANNELS;
    const unsigned int in_size = SOFTMAX_CMP_LAYER_BATCH_SIZE*fm_size;
    const unsigned int out_size = SOFTMAX_CMP_LAYER_BATCH_SIZE;

    // test images
    static softmax_cmp_layer_data_t test_in[in_size][1];
    static softmax_cmp_layer_ctrl_t test_out[out_size][SOFTMAX_CMP_LAYER_CTRL];

    // load input
    load_data_l<
        SOFTMAX_CMP_LAYER_BATCH_SIZE,
        SOFTMAX_CMP_LAYER_CHANNELS*SOFTMAX_CMP_LAYER_ROWS*SOFTMAX_CMP_LAYER_COLS,
        1, //doesn't really have coarse
        softmax_cmp_layer_data_t
    >(input_path,test_in);

    // load output
    load_data_l<
        SOFTMAX_CMP_LAYER_BATCH_SIZE,
        1,
        SOFTMAX_CMP_LAYER_CTRL, //acts like a coarse
        softmax_cmp_layer_ctrl_t
    >(output_path,test_out);

    // convert to streams
    to_stream_l<
        SOFTMAX_CMP_LAYER_BATCH_SIZE,
        SOFTMAX_CMP_LAYER_CHANNELS*SOFTMAX_CMP_LAYER_ROWS*SOFTMAX_CMP_LAYER_COLS,
        1,
        softmax_cmp_layer_data_t
    >(test_in,in);

    to_stream_l<
        SOFTMAX_CMP_LAYER_BATCH_SIZE,
        1,
        SOFTMAX_CMP_LAYER_CTRL, //acts like a coarse
        softmax_cmp_layer_ctrl_t
    >(test_out,out_correct);

    softmax_cmp_layer_top(in,out);
    
    for(int i=0;i<SOFTMAX_CMP_LAYER_CTRL;i++)
    {
        printf("TESTING OUTPUT %d: ",i);
        //err += checkStreamEqual<b_data_t>(out[i],out_correct[i],true);
        err += checkStreamEqual<b_bool_t>(out[i],out_correct[i],true);
        printf("%s\n",(err==0) ? "passed" : "failed");
    }

    return err;
}
