#ifndef COMMON_TB_HPP_
#define COMMON_TB_HPP_

#include "common.hpp"
#include <string>
#include <iostream>
#include <fstream>
#include <typeinfo>
#include <stdio.h>
#include <stdlib.h>

//////////////////////////////////////////////////////////////////////
/////////////////////////////// LAYERS ///////////////////////////////
//////////////////////////////////////////////////////////////////////
template<int BATCH_SIZE, int SIZE, int STREAMS, typename T>
void load_data_l(
    std::string filepath,
    T data[SIZE*BATCH_SIZE][STREAMS]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    //int index = 0;
    int bidx=0;
    for(int i=0;i<SIZE*BATCH_SIZE;i++) {
        if (i % SIZE == 0 && i != 0) {
            bidx++;
        }
        for(int j=0;j<STREAMS;j++) {
            float val;
            fscanf(fp,"%f\n", &val);
            //data[i][j] = T( val );
            data[i][j].batchid = bidx;
            data[i][j].data = ( val );
        }
    }

    // close file
    fclose(fp);
}

/* LAYER but also GLUE output, and squeeze */
template<int SIZE, int STREAMS, typename T>
void load_data(
    std::string filepath,
    T data[SIZE][STREAMS]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    int index = 0;
    for(int i=0;i<SIZE;i++) {
        for(int j=0;j<STREAMS;j++) {
            float val;
            fscanf(fp,"%f\n", &val);
            //data[i][j] = T( val );
            data[i][j].batchid = 7;
            data[i][j].data = ( val );
        }
    }

    // close file
    fclose(fp);
}

/* STANDARD FOR TESTING LAYER INPUTS */
template<int BATCH_SIZE,int SIZE, int STREAMS, typename T>
void to_stream_l(
    T in[SIZE*BATCH_SIZE][STREAMS],
    stream_t(T) out[STREAMS]
) {
    for(int i=0;i<SIZE*BATCH_SIZE;i++) {
        for(int j=0;j<STREAMS;j++) {
 	        out[j].write(in[i][j]);
	    }
    }
}
/* testing split layer out */
template<int BATCH_SIZE,int SIZE, int COARSE, int PORTS, typename T>
void to_stream_l(
    T in[SIZE*BATCH_SIZE][PORTS][COARSE],
    stream_t(T) out[PORTS][COARSE]
) {
    for(int i=0;i<SIZE*BATCH_SIZE;i++) {
        for(int j=0;j<PORTS;j++) {
            for(int k=0;k<COARSE;k++) {
 	            out[j][k].write(in[i][j][k]);
            }
	    }
    }
}
/* STANDARD FOR TESTING LAYER INPUTS */
template<int SIZE, int STREAMS, typename T>
void to_stream(
    T in[SIZE][STREAMS],
    stream_t(T) out[STREAMS]
) {
    for(int i=0;i<SIZE;i++) {
        for(int j=0;j<STREAMS;j++) {
 	        out[j].write(in[i][j]);
	    }
    }
}
/* DEBUG VERSION */
template<int SIZE, int STREAMS, bool debug, typename T>
void to_stream(
    T in[SIZE][STREAMS],
    stream_t(T) out[STREAMS]
) {
    std::cout<<"WARNING: TO STREAM DEBUG VERSION, size:"<<SIZE<<std::endl;
    for(int i=0;i<SIZE;i++) {
        for(int j=0;j<STREAMS;j++) {
            std::cout<<"to stream size idx:"<<i<<std::endl;
 	        out[j].write(in[i][j]);
	    }
    }
}

/* (BUFFER LAYER OUT LOAD) */
template<int FM_SIZE, int COARSE, typename T>
void load_data_buffout(
    std::string filepath,
    std::vector<T> data[COARSE] 
) {
    // read in file
    std::ifstream input_file(filepath);
    float val;

    // check file opened
    if (!input_file.is_open()) {
        perror("Failed: ");
    }
    
    // save to array
    T caster;
    int i=0;
    while(input_file >> val) {
        caster.data = val;
        data[i].push_back(caster);
        i++;
        if (i>=COARSE){ i=0; }; //reset i every COARSE number of items
        /*if (i==0){
            data_t tmp[COARSE];
        }
        tmp[i] = data_t(val);
        if (i>=COARSE){
            data.push_back(tmp);
        }
        i++;*/
    }
    // close file
    input_file.close();

    //FIXME some other way:
    //adding flush data
    for (int fidx=0; fidx<FM_SIZE; fidx++) {
        for (int crs_idx=0;crs_idx<COARSE;crs_idx++) {
            caster.data = 6.9;
            data[crs_idx].push_back( caster );
        }
    }
}
/* old version (BUFFER LAYER OUT LOAD) */
template<int COARSE, typename T>
void load_data(
    std::string filepath,
    std::vector<T> data[COARSE] 
) {
    // read in file
    std::ifstream input_file(filepath);
    float val;

    // check file opened
    if (!input_file.is_open()) {
        perror("Failed: ");
    }
    
    // save to array
    T caster;
    int i=0;
    while(input_file >> val) {
        caster.data = val;
        data[i].push_back(caster);
        i++;
        if (i>=COARSE){ i=0; }; //reset i every COARSE number of items
        /*if (i==0){
            data_t tmp[COARSE];
        }
        tmp[i] = data_t(val);
        if (i>=COARSE){
            data.push_back(tmp);
        }
        i++;*/
    }
    
    // close file
    input_file.close();
}

/* BUFFER OUT VARIABLE SIZE */
template<int COARSE,typename T>
void to_stream(
    std::vector<T> in[COARSE],
    stream_t(T) out[COARSE],
    int vec_size
) {
    for(int i=0;i<vec_size;i++) {
        for(int c=0;c<COARSE;c++) {
	        out[c].write(in[c][i]);
        }
    }
}

/* GREATER(CMP layer) DUPE INPUT */
template<int SIZE, int STREAMS, typename T>
void load_data_dupe(
    std::string filepath,
    T data[SIZE][STREAMS]
) {
    // read in file
    std::ifstream input_file(filepath);

    // check file opened
    if (!input_file.is_open()) {
    //if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    int index = 0;
    int size_idx=0;
    float val;
    while(input_file >> val) {
        for(int j=0;j<STREAMS;j++) {
            data[size_idx][j] = T( val );
        } 
        size_idx++;
    }
    input_file.close(); // close file
}

///////////////////////////////////////////////////////////////////////
/////////////////////////////// MODULES ///////////////////////////////
///////////////////////////////////////////////////////////////////////

/* (ACCUM) */
template<int SIZE, typename T>
void load_data(
    std::string filepath,
    T data[SIZE]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    for(int i=0;i<SIZE;i++) {
        float val;
        fscanf(fp,"%f\n", &val);
        //data[i] = T( val );
        data[i].batchid = 7;
        data[i].data = ( val );
    }

    // close file
    fclose(fp);
}
/* BUFFER and other batched modules */
template<int BATCH_SIZE, int SHAPE_SIZE, typename T>
void load_data_buff(
    std::string filepath,
    T data[BATCH_SIZE*SHAPE_SIZE]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    int bidx = 0;
    for(int i=0;i<BATCH_SIZE*SHAPE_SIZE;i++) {
        if (i % SHAPE_SIZE == 0 && i != 0) {
            bidx++;
        }
        float val;
        fscanf(fp,"%f\n", &val);
        data[i].batchid = bidx;
        data[i].data = ( val );
    }

    // close file
    fclose(fp);
}
/* EXIT MERGE */
template<int BATCH_SIZE, int SHAPE_SIZE, int BATCH_OFFSET, typename T>
void load_data_em(
    std::string filepath,
    T data[BATCH_SIZE*SHAPE_SIZE]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    int bidx = BATCH_OFFSET;
    for(int i=0;i<BATCH_SIZE*SHAPE_SIZE;i++) {
        if (i % SHAPE_SIZE == 0 && i != 0) {
            bidx++;
        }
        float val;
        fscanf(fp,"%f\n", &val);
        data[i].batchid = bidx;
        data[i].data = ( val );
    }

    // close file
    fclose(fp);
}
// bias loading 
template<int SIZE, typename T>
void load_data_b(
    std::string filepath,
    T data[SIZE]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    for(int i=0;i<SIZE;i++) {
        float val;
        fscanf(fp,"%f\n", &val);
        data[i] = T( val );
    }

    // close file
    fclose(fp);
}

template<int SIZE, typename T>
void to_stream(
    T in[SIZE],
    stream_t(T) &out
)
{
    for(int i=0;i<SIZE;i++) {
 	out.write(in[i]);
    }
}
/* exit merge module test, anti flush*/
template<int SIZE, int FLUSH_SIZE, typename T>
void to_stream_ex(
    T in[SIZE],
    stream_t(T) &out
)
{
    for(int i=0;i<SIZE;i++) {
 	    out.write(in[i]);
    }

    //T flusher;
    //flusher.batchid = 420;
    //flusher.data = 6.9;
    //for(int i=0;i<FLUSH_SIZE;i++) {
    //    out.write(flusher);
    //}
}

/* (weights only because of new default types) */
template<int SIZE, int KERNEL_SIZE_X, int KERNEL_SIZE_Y, typename T>
void load_data_w(
    std::string filepath,
    T data[SIZE][KERNEL_SIZE_X][KERNEL_SIZE_Y]
) {

    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }
     // save to array
    for(int i=0;i<SIZE;i++) {
        for(int k1=0;k1<KERNEL_SIZE_X;k1++) {
            for(int k2=0;k2<KERNEL_SIZE_Y;k2++) {
                float val;
                fscanf(fp,"%f\n", &val);
                data[i][k1][k2] = T(val);
	        }
	    }
    }

    // close file
    fclose(fp);
}
/* (CONV,POOL, FORK in) */
template<int SIZE, int KERNEL_SIZE_X, int KERNEL_SIZE_Y, typename T>
void load_data(
    std::string filepath,
    T data[SIZE][KERNEL_SIZE_X][KERNEL_SIZE_Y]
) {

    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }
     // save to array
    for(int i=0;i<SIZE;i++) {
        for(int k1=0;k1<KERNEL_SIZE_X;k1++) {
            for(int k2=0;k2<KERNEL_SIZE_Y;k2++) {
                float val;
                fscanf(fp,"%f\n", &val);
                T tmp;
                //FIXME include CORRECT batch info
                tmp.batchid=7;
                tmp.data=val;
                data[i][k1][k2] = tmp;
	        }
	    }
    }

    // close file
    fclose(fp);
}

template<int SIZE, int KERNEL_SIZE_X, int KERNEL_SIZE_Y, typename T>
void to_stream(
    T in[SIZE][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(T) out[KERNEL_SIZE_X][KERNEL_SIZE_Y]
) {
    for(int i=0;i<SIZE;i++) {
        for(int k1=0;k1<KERNEL_SIZE_X;k1++) {
            for(int k2=0;k2<KERNEL_SIZE_Y;k2++) {
                out[k1][k2].write(in[i][k1][k2]);
            }
	    }
    }
}

/* (FORK out only) */
template<int SIZE, int COARSE, int KERNEL_SIZE_X, int KERNEL_SIZE_Y, typename T>
void load_data(
    std::string filepath,
    T data[SIZE][COARSE][KERNEL_SIZE_X][KERNEL_SIZE_Y]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    for(int i=0;i<SIZE;i++) {
        for(int c=0;c<COARSE;c++) {
            for(int k1=0;k1<KERNEL_SIZE_X;k1++) {
                for(int k2=0;k2<KERNEL_SIZE_Y;k2++) {
                    float val;
                    fscanf(fp,"%f\n", &val);
                    //data[i][c][k1][k2] = T(val);
                    T tmp;
                    tmp.batchid=7;
                    tmp.data=val;
                    data[i][c][k1][k2] = tmp;
                }
            }
        }
    }

    // close file
    fclose(fp);
}

template<int SIZE, int COARSE, int KERNEL_SIZE_X, int KERNEL_SIZE_Y, typename T>
void to_stream(
    T in[SIZE][COARSE][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(T) out[COARSE][KERNEL_SIZE_X][KERNEL_SIZE_Y]
) {
    for(int i=0;i<SIZE;i++) {
        for(int c=0;c<COARSE;c++) {
            for(int k1=0;k1<KERNEL_SIZE_X;k1++) {
	            for(int k2=0;k2<KERNEL_SIZE_Y;k2++) {
	                out[c][k1][k2].write(in[i][c][k1][k2]);
                }
	        }
        }
    }
}

/* (WEIGHTS_INTR) */
template<int COARSE_IN, int COARSE_OUT, int CHANNELS, int FILTERS, int KERNEL_SIZE_X, int KERNEL_SIZE_Y, typename T>
void load_data(
    std::string filepath,
    T data[COARSE_IN][COARSE_OUT][DIVIDE(CHANNELS,COARSE_IN)*DIVIDE(FILTERS,COARSE_OUT)][KERNEL_SIZE_X][KERNEL_SIZE_Y]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    const int channels_per_coarse_in = DIVIDE(CHANNELS,COARSE_IN);
    const int filters_per_coarse_out = DIVIDE(FILTERS,COARSE_OUT);

    // save to array
    for(int i=0;i<channels_per_coarse_in;i++) {
        for(int cin=0;cin<COARSE_IN;cin++) {
            for(int j=0;j<filters_per_coarse_out;j++) {
                for(int cout=0;cout<COARSE_OUT;cout++) {
                    for(int k1=0;k1<KERNEL_SIZE_X;k1++) {
                        for(int k2=0;k2<KERNEL_SIZE_Y;k2++) {
                            float val;
                            fscanf(fp,"%f\n", &val);
                            //int index = (i*COARSE_IN+cin)*filters_per_coarse_out+j*COARSE_OUT+cout;
                            int index = i*filters_per_coarse_out+j;
                            //data[cin][cout][index][k1][k2] = T(val);
                            data[cin][cout][index][k1][k2].data = (val);
                        }
                    }
                }
            }
        }
    }

    // close file
    fclose(fp);
}

/* (WEIGHTS_INTR) */
template<int COARSE_IN, int COARSE_OUT, int CHANNELS, int FILTERS, typename T>
void load_data(
    std::string filepath,
    T data[COARSE_IN][COARSE_OUT][DIVIDE(CHANNELS,COARSE_IN)*DIVIDE(FILTERS,COARSE_OUT)]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    const int channels_per_coarse_in = DIVIDE(CHANNELS,COARSE_IN);
    const int filters_per_coarse_out = DIVIDE(FILTERS,COARSE_OUT);

    // save to array
    for(int i=0;i<channels_per_coarse_in;i++) {
        for(int cin=0;cin<COARSE_IN;cin++) {
            for(int j=0;j<filters_per_coarse_out;j++) {
                for(int cout=0;cout<COARSE_OUT;cout++) {
                    float val;
                    fscanf(fp,"%f\n", &val);
                    int index = i*filters_per_coarse_out+j;
                    //data[cin][cout][index] = T(val);
                    data[cin][cout][index].data = (val);
                }
            }
        }
    }

    // close file
    fclose(fp);
}


template<int SIZE, int COARSE_IN, int COARSE_OUT, int KERNEL_SIZE_X, int KERNEL_SIZE_Y, typename T>
void to_stream(
    T in[COARSE_IN][COARSE_OUT][SIZE][KERNEL_SIZE_X][KERNEL_SIZE_Y],
    stream_t(T) out[COARSE_IN][COARSE_OUT][KERNEL_SIZE_X][KERNEL_SIZE_Y]
) {
    for(int cin=0;cin<COARSE_IN;cin++) {
        for(int cout=0;cout<COARSE_OUT;cout++) {
            for(int i=0;i<SIZE;i++) {
                for(int k1=0;k1<KERNEL_SIZE_X;k1++) {
                    for(int k2=0;k2<KERNEL_SIZE_Y;k2++) {
                        out[cin][cout][k1][k2].write(in[cin][cout][i][k1][k2]);
                    }
                }
	    }
        }
    }
}

/* /1* (WEIGHTS_INTR) *1/ */
/* template<int SIZE, int COARSE_IN, int COARSE_OUT, typename T> */
/* void load_data( */
/*     std::string filepath, */
/*     T data[COARSE_IN][COARSE_OUT][SIZE] */
/* ) { */
/*     // read in file */
/*     const char *filepath_cstr = filepath.c_str(); */
/*     FILE * fp = fopen(filepath_cstr,"r"); */

/*     // check file opened */
/*     if (fp == NULL) { */
/*         perror("Failed: "); */
/*     } */

/*     // save to array */
/*     for(int cin=0;cin<COARSE_IN;cin++) { */
/*         for(int cout=0;cout<COARSE_OUT;cout++) { */
/*             for(int i=0;i<SIZE;i++) { */
/*                 float val; */
/*                 fscanf(fp,"%f\n", &val); */
/*                 data[cin][cout][i] = T(val); */
/*             } */
/*         } */
/*     } */

/*     // close file */
/*     fclose(fp); */
/* } */

template<int SIZE, int COARSE_IN, int COARSE_OUT, typename T>
void to_stream(
    T in[COARSE_IN][COARSE_OUT][SIZE],
    stream_t(T) out[COARSE_IN][COARSE_OUT]
) {
    for(int cin=0;cin<COARSE_IN;cin++) {
        for(int cout=0;cout<COARSE_OUT;cout++) {
            for(int i=0;i<SIZE;i++) {
                out[cin][cout].write(in[cin][cout][i]);
	    }
        }
    }
}

/* (WEIGHTS_INTR) */
template<int SIZE, int COARSE_IN, int COARSE_OUT, int FINE, typename T>
void load_data(
    std::string filepath,
    T data[COARSE_IN][COARSE_OUT][SIZE][FINE]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    for(int cin=0;cin<COARSE_IN;cin++) {
        for(int cout=0;cout<COARSE_OUT;cout++) {
            for(int i=0;i<SIZE;i++) {
                for(int f=0;f<FINE;f++) {
                    float val;
                    fscanf(fp,"%f\n", &val);
                    //data[cin][cout][i][f] = T(val);
                    data[cin][cout][i][f].data = (val);
                }
            }
        }
    }

    // close file
    fclose(fp);
}

template<int SIZE, int COARSE_IN, int COARSE_OUT, int FINE, typename T>
void to_stream(
    T in[COARSE_IN][COARSE_OUT][SIZE][FINE],
    stream_t(T) out[COARSE_IN][COARSE_OUT][FINE]
) {
    for(int cin=0;cin<COARSE_IN;cin++) {
        for(int cout=0;cout<COARSE_OUT;cout++) {
            for(int i=0;i<SIZE;i++) {
                for(int f=0;f<FINE;f++) {
                    out[cin][cout][f].write(in[cin][cout][i][f]);
                }
	    }
        }
    }
}


/* (GLUE) */
/* same as CONV/POOL */
/*template<int SIZE, int COARSE_IN, int COARSE_OUT, typename T>
void load_data(
    std::string filepath,
    T data[SIZE][COARSE_IN][COARSE_OUT]
) {

    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }

    // save to array
    for(int i=0;i<SIZE;i++) {
        for(int a=0;a<COARSE_IN;a++) {
            for(int b=0;b<COARSE_OUT;b++) {
                float val;
                fscanf(fp,"%f\n", &val);
                data[i][a][b] = T(val);
	    }
        }
    }

    // close file
    fclose(fp);
}

template<int SIZE, int COARSE_IN, int COARSE_OUT, typename T>
void to_stream(
    T in[SIZE][COARSE_IN][COARSE_OUT],
    stream_t(T) out[COARSE_IN][COARSE_OUT]
) {
    for(int i=0;i<SIZE;i++) {
        for(int a=0;a<COARSE_IN;a++) {
            for(int b=0;b<COARSE_OUT;b++) {
	        out[a][b].write(in[i][a][b]);
	    }
        }
    }
}*/

/* (COMPARE_THR) */
template<typename T>
void load_data(
    std::string filepath,
    T data[1]
) {
    // read in file
    const char *filepath_cstr = filepath.c_str(); 
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed: ");
    }
    
    // save to array
    //for(int i=0;i<SIZE;i++) {
    float val;
    fscanf(fp,"%f\n", &val);
    //data[0] = val;
    data[0].data = val;
    //}
    
    // close file
    fclose(fp);
}

/* (BUFFER MOD OUT LOAD) */
template<int FM_SIZE, typename T>
void load_data_buffout(
    std::string filepath,
    std::vector<T> &data 
) {
    // read in file
    std::ifstream input_file(filepath);
    float val;

    // check file opened
    if (!input_file.is_open()) {
        perror("Failed: ");
    }
    
    // save to array
    int i=0;
    T tmp;
    while(input_file >> val) {
        tmp.data = val;
        data.push_back( tmp );
        i++;
    }
    // close file
    input_file.close();

    //FIXME some other way:
    //adding flush data
    for (int fidx=0; fidx<FM_SIZE; fidx++) {
        tmp.batchid = 420;
        tmp.data = 6.9;
        data.push_back( tmp );
    }
    
}

/* FIXME OLD VERSION (BUFFER MOD OUT LOAD) */
template<typename T>
void load_data(
    std::string filepath,
    std::vector<T> &data 
) {
    // read in file
    std::ifstream input_file(filepath);
    float val;

    // check file opened
    if (!input_file.is_open()) {
        perror("Failed: ");
    }
    
    // save to array
    int i=0;
    T tmp;
    while(input_file >> val) {
        tmp.data = val;
        data.push_back( tmp );
        i++;
    }
    
    // close file
    input_file.close();
}

/* BUFFER OUT VARIABLE SIZE - LAYER VERSION*/
template<int COARSE, typename T, typename T2>
void to_stream(
    std::vector<T> in[COARSE],
    std::vector<T2> b_in,
    stream_t(T) out[COARSE],
    int shape_size
) {
    int bidx=0;
    T out_val;
    for(int i=0;i<(b_in.size()*shape_size);i++) {
        if (i % shape_size == 0 && i != 0) {
            bidx++;
        }
        for(int c=0;c<COARSE;c++) {
            out_val.batchid = b_in[bidx];
            out_val.data = in[c][i].data;
	        out[c].write(out_val);
        }
    }
}
/* BUFFER OUT VARIABLE SIZE - MODULE VERSION*/
template<typename T, typename T2>
void to_stream(
    std::vector<T> in,
    std::vector<T2> b_in,
    stream_t(T) &out,
    int shape_size
) {
    int bidx=0;
    T out_val;
    for(int i=0;i<(b_in.size()*shape_size);i++) {
        if (i % shape_size == 0 && i != 0) {
            bidx++;
        }
        out_val.batchid = b_in[bidx];
        out_val.data = in[i].data;
	    out.write(out_val);
    }
}

////////////////////////////////////////////////
////////// CHECK STREAM TO VALID OUTPUT ////////
////////////////////////////////////////////////

template<typename T>
int checkStreamEqual(
		stream_t(T) &test,
		stream_t(T) &valid,
		bool print_out=false
)
{
    int err = 0;
    while(!valid.empty())
	{
		if(test.empty())
		{
			printf("ERROR: empty early\n");
			return 1;
		}
		//T tmp = test.read();
		//T tmp_valid = valid.read();
        T tmp;
        T tmp_valid;
        test.read_nb(tmp);
        valid.read_nb(tmp_valid);
        //float conversion for visual comparison
        float tmpf,tmpf_valid;
        tmpf=tmp.data.to_float();
        tmpf_valid=tmp_valid.data.to_float();

		if(print_out) {
            //printf("%x,%x\n",tmp.range()&BIT_MASK,tmp_valid.range()&BIT_MASK);
            //std::cout<<"Expected:"<<tmp.range()&BIT_MASK
            //    <<" Actual:"<<tmp_valid.range()&BIT_MASK<<std::endl;    
            std::cout<<"Expected:"<<tmpf
                <<" Actual:"<<tmpf_valid<<std::endl;    
        }
		if(
				(tmp.data.to_float() > tmp_valid.data.to_float()+ERROR_TOLERANCE) ||
				(tmp.data.to_float() < tmp_valid.data.to_float()-ERROR_TOLERANCE)
		)
		{
			//printf("ERROR: wrong value\n");
			printf("ERROR: wrong value. Actual:%f, Expected:%f, Difference:%f\n",
                    tmp.data.to_float(), tmp_valid.data.to_float(), tmp.data.to_float()-tmp_valid.data.to_float());
			//return 1;
			err++;
		}
        if (tmp.batchid != tmp_valid.batchid) {
            uint16_t printer = tmp.batchid;
            uint16_t printer2 = tmp_valid.batchid;
			printf("ERROR: wrong ID. Actual:%d, Expected:%d\n",
                    printer, printer2 );
			err++;
        }
	}

	if(!test.empty())
	{
		printf("ERROR: still data in stream\n");
		return 1;
		err++;
	}
	return err;
}
template<typename T>
int checkStreamEqual_EM(
        int fm_size,
		stream_t(T) &test,
		stream_t(T) &valid,
		bool print_out=false
) 
{
    int fm_cntr=0;
    int err = 0;
    T id_str;
    while(!valid.empty()) {
		if(test.empty()) {
			printf("ERROR: empty early\n");
			return 1;
		}
		//T tmp = test.read();
		//T tmp_valid = valid.read();
        T tmp;
        T tmp_valid;
        test.read_nb(tmp);
        valid.read_nb(tmp_valid);
        //float conversion for visual comparison
        float tmpf,tmpf_valid;
        tmpf=tmp.data.to_float();
        tmpf_valid=tmp_valid.data.to_float();

		if(print_out) {
            //printf("%x,%x\n",tmp.range()&BIT_MASK,tmp_valid.range()&BIT_MASK);
            //std::cout<<"Expected:"<<tmp.range()&BIT_MASK
            //    <<" Actual:"<<tmp_valid.range()&BIT_MASK<<std::endl;    
            std::cout<<"Expected:"<<tmpf
                <<" Actual:"<<tmpf_valid
                <<"fm ctr:"<<fm_cntr<<std::endl;    
        }
		//if(
		//		(tmp.data.to_float() > tmp_valid.data.to_float()+ERROR_TOLERANCE) ||
		//		(tmp.data.to_float() < tmp_valid.data.to_float()-ERROR_TOLERANCE)
		//)
		//{
		//	//printf("ERROR: wrong value\n");
		//	printf("ERROR: wrong value. Actual:%f, Expected:%f, Difference:%f\n",
        //            tmp.data.to_float(), tmp_valid.data.to_float(), tmp.data.to_float()-tmp_valid.data.to_float());
		//	//return 1;
		//	err++;
		//}
        if (fm_cntr == 0 ) {
            // up date the batch id every fm_size values
            id_str.batchid = tmp.batchid;
        } else {
            if (tmp.batchid != id_str.batchid) {
                printf("ERROR: wrong ID. Actual:%d, Expected:%d\n",
                        tmp.batchid, id_str.batchid); //tmp_valid.batchid );
                err++;
            }
        }
        // count up to fm size
        fm_cntr++;
        fm_cntr = fm_cntr%fm_size;

	}

	if(!test.empty())
	{
		printf("ERROR: still data in stream\n");
		return 1;
		err++;
	}
	return err;
}
// bool version
template<>
int checkStreamEqual <b_bool_t> (
		hls::stream <b_bool_t> &test,
		hls::stream <b_bool_t> &valid,
		bool print_out
)
{
    int err=0;
	while(!valid.empty())
	{
		if(test.empty())
		{
			printf("ERROR: empty early\n");
			return 1;
		}
		b_bool_t tmp = test.read();
		b_bool_t tmp_valid = valid.read();

		if(print_out) printf("test val:%d, valid val:%d\n",tmp.data,tmp_valid.data);

		if( tmp.data != tmp_valid.data) {
			//printf("ERROR: wrong value\n");
            printf("ERROR: wrong value Actual:%d, Expected:%d \n",tmp.data, tmp_valid.data);
			err++;
		}
        if (tmp.batchid != tmp_valid.batchid) {
			printf("ERROR: wrong ID. Actual:%d, Expected:%d\n",
                    tmp.batchid, tmp_valid.batchid );
			err++;
        }
	}

	if(!test.empty())
	{
		printf("ERROR: still data in stream\n");
		err++;
	}
	return err;
}

template<>
int checkStreamEqual <b_float_t> (
		hls::stream <b_float_t> &test,
		hls::stream <b_float_t> &valid,
		bool print_out
)
{
    int err=0;
	while(!valid.empty())
	{
		if(test.empty())
		{
			printf("ERROR: empty early\n");
			return 1;
		}
		b_float_t tmp = test.read();
		b_float_t tmp_valid = valid.read();

		if(print_out) printf("test:%f,valid:%f\n",tmp.data,tmp_valid.data);

		if(
				(tmp.data > tmp_valid.data+ERROR_TOLERANCE) ||
				(tmp.data < tmp_valid.data-ERROR_TOLERANCE)
		)
		{
			//printf("ERROR: wrong value\n");
			printf("ERROR: wrong value Actual:%f, Expected:%f \n",tmp.data, tmp_valid.data);
			err++;
		}
        if (tmp.batchid != tmp_valid.batchid) {
			printf("ERROR: wrong ID. Actual:%d, Expected:%d\n",
                    tmp.batchid, tmp_valid.batchid );
			err++;
        }
	}

	if(!test.empty())
	{
		printf("ERROR: still data in stream\n");
		err++;
	}
	return err;
}

template<int SIZE>
int check_array_equal(
    volatile mem_int test[SIZE],
    volatile mem_int valid[SIZE]
)
{
    int err = 0;
    for(int i=0;i<SIZE;i++) {
        for(int j=0;j<1;j++) {
            data_t tmp, tmp_valid;
            tmp.range()         = (test[i] >> j*DATA_WIDTH) & BIT_MASK;
            tmp_valid.range()   = (valid[i]>> j*DATA_WIDTH) & BIT_MASK;
            if(
                (tmp.to_float() > tmp_valid.to_float()+ERROR_TOLERANCE) ||
                (tmp.to_float() < tmp_valid.to_float()-ERROR_TOLERANCE)
            ){
                err += 1;
                printf("ERROR (%d,%d): recorded:%f, expected:%f\n",i,j,tmp.to_float(),tmp_valid.to_float());
            }
        }
    }
    return err;
}
template<typename T>
int checkStreamEqual_file(
		stream_t(T) &test,
		stream_t(T) &valid,
		bool print_out,
		std::ofstream& fid
)
{
	char byte[4];
	while(!valid.empty())
	{
		if(test.empty())
		{
			printf("ERROR: empty early\n");
			return 1;
		}
		T tmp = test.read();
		T tmp_valid = valid.read();

		if (fid)
		{
			byte[0] = tmp.range(7,0);
			byte[1] = tmp.range(15,8);
			byte[2] = 0;
			byte[3] = 0;
			fid.write(byte,4);
		}

		if(print_out) printf("%f,%f\n",tmp.data.to_float(),tmp_valid.data.to_float());

		if(
				(tmp.data.to_float() > tmp_valid.data.to_float()+ERROR_TOLERANCE) ||
				(tmp.data.to_float() < tmp_valid.data.to_float()-ERROR_TOLERANCE)
		)
		{
			printf("ERROR: wrong value\n");
			return 1;
		}
	}

	if(!test.empty())
	{
		printf("ERROR: still data in stream\n");
		return 1;
	}
	return 0;
}

////////////////////////////////////////////////////
////////// LOAD DATA FOR PARTITION TESTS ///////////
////////////////////////////////////////////////////

template<
    int INPUTS,
    int SIZE,
    int WR_FACTOR=1
>
void load_net_weights(
    std::string filepath,
    volatile mem_int data[INPUTS][DIVIDE(SIZE,INPUTS)],
    int wr_index = 0
)
{
    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed to load weights at");
    }

    for(int w=0;w<WR_FACTOR;w++) {
        for(int i=0;i<INPUTS;i++) {
            for(int j=0;j<DIVIDE(SIZE,INPUTS);j++) {
                // read in the value from the file
                mem_int val;
                fscanf(fp,"%l\n", &val);
                // add to the input if correct weights reloading index
                if ( w == wr_index ) {
                    data[i][j] = val;
                }
           }
        }
    }
    // close file
    fclose(fp);
}

template<
    int INPUTS,
    int BATCH_SIZE,
    int ROWS,
    int COLS,
    int CHANNELS,
    int STREAMS,
    int WR_FACTOR=1
>
void load_net_data(
    std::string filepath,
    volatile mem_int data[INPUTS][BATCH_SIZE*ROWS*COLS*DIVIDE(CHANNELS,STREAMS)*WR_FACTOR],
    int wr_index = 0
)
{

    // read in file
    const char *filepath_cstr = filepath.c_str();
    FILE * fp = fopen(filepath_cstr,"r");

    // check file opened
    if (fp == NULL) {
        perror("Failed to load data at");
    }

    // get variables
    int channels_per_stream = DIVIDE(CHANNELS,STREAMS);
    int dma_channels = DIVIDE(DMA_WIDTH,DATA_WIDTH);

    // save to array
    for(int i=0;i<BATCH_SIZE*ROWS*COLS;i++) {
        for(int j=0;j<WR_FACTOR;j++) {
            for(int k=0;k<channels_per_stream;k++) {
                // read in the value from the file
                mem_int val;
                fscanf(fp,"%ld\n", &val);
                // specific weights reloading index
                if (j == wr_index) {
                    int out_index = i*channels_per_stream*WR_FACTOR + j*channels_per_stream + k;
                    data[0][out_index] = val;
                }
            }
        }
    }
    // close file
    fclose(fp);
}

#endif
