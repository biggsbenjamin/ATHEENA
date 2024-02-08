#include "common_tb.hpp"
#include "glue_tb.hpp"

int main() {
    // variable initialisation
    stream_t(glue_acc_t) in;
    stream_t(glue_data_t) out;

    // dimensions
    const int size_in  = GLUE_BATCH_SIZE*GLUE_ROWS*GLUE_COLS*DIVIDE(GLUE_FILTERS,GLUE_COARSE_OUT);
    const int size_out = GLUE_BATCH_SIZE*GLUE_ROWS*GLUE_COLS*DIVIDE(GLUE_FILTERS,GLUE_COARSE_OUT);

    // gen input
    coarse_in_loop: for(int i=0;i<GLUE_COARSE_IN;i++) {
        coarse_out_loop: for(int j=0;j<GLUE_COARSE_OUT;j++) {
            gen_stream<glue_acc_t,size_in>(in[i][j]);
        }
    }

    // run component
    glue_top(in,out);

}
