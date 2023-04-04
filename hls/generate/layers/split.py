# import modules
import os
import shutil

#import generate.modules.fork

split_layer_template_header = """//auto generated
#ifndef {NAME}_HPP_
#define {NAME}_HPP_

#include "split.hpp"

#define name        {name}
#define {NAME}_ID   {id}

typedef b_data_t {name}_data_t;
typedef {name}_data_t {name}_input_t;
typedef {name}_data_t {name}_output_t;

#define {NAME}_BATCH_SIZE   {batch_size}
#define {NAME}_ROWS         {rows}
#define {NAME}_COLS         {cols}
#define {NAME}_CHANNELS     {channels}
#define {NAME}_CHANNELS_PM  {channels_per_module}
#define {NAME}_COARSE       {coarse}
#define {NAME}_PORTS_OUT    {ports_out}

#define {NAME}_COARSE_IN    {NAME}_COARSE
#define {NAME}_COARSE_OUT   {NAME}_COARSE

/**
 * FUNCTION DEFINITION
 */

void {name}(
    stream_t({name}_input_t)  in[{NAME}_COARSE],
    stream_t({name}_output_t) out[{NAME}_PORTS_OUT][{NAME}_COARSE],
    int mode
);

#undef name
#endif
"""

split_layer_template_src = """//auto generated
#include "{name}.hpp"

void {name}(
    stream_t({name}_input_t)  in[{NAME}_COARSE],
    stream_t({name}_output_t) out[{NAME}_PORTS_OUT][{NAME}_COARSE],
    int mode
)
{{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

#pragma HLS STREAM variable=in depth={buffer_depth}
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in  complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0

    split<
        {NAME}_BATCH_SIZE,
        {NAME}_ROWS,
        {NAME}_COLS,
        {NAME}_CHANNELS_PM,
        {NAME}_COARSE,
        {NAME}_PORTS_OUT,
        {name}_data_t
    >(in,out);

}}
"""

split_layer_top_template_src = """//auto generated
#include "{name}.hpp"

void {name}_top(
    stream_t({name}_input_t)  in[{NAME}_COARSE],
    stream_t({name}_output_t) out[{NAME}_PORTS_OUT][{NAME}_COARSE]
)
{{

#pragma HLS DATAFLOW

#pragma HLS INTERFACE s_axilite port=return bundle=ctrl
#pragma HLS INTERFACE axis port=in
#pragma HLS INTERFACE axis port=out

#pragma HLS STREAM variable=in //depth={buffer_depth}
#pragma HLS STREAM variable=out
    int mode=0;

    {name}(in,out,mode);

}}

"""

def gen_split_layer(name,param,src_path,header_path, topless=True):

    ## FORK MODULE INIT
    #fork = generate.modules.fork.gen_fork_module(
    #    name+"_fork",
    #    "in[coarseIndex]",
    #    "out[coarseIndex]",
    #    indent=8
    #)

    # src
    split_layer_src = split_layer_template_src.format(
        name            =name,
        NAME            =name.upper(),
        buffer_depth=max(param['buffer_depth'],2)#,
        #fork            =fork
    )

    # header
    split_layer_header = split_layer_template_header.format(
        name                =name,
        NAME                =name.upper(),
        id                  =0, # param['id'],
        batch_size          =param['batch_size'],
        rows                =param['rows_in'],
        cols                =param['cols_in'],
        channels            =param['channels_in'],
        channels_per_module =int(param['channels_in']/(param['coarse_in'])),
        coarse              =param['coarse_in'],
        #rows_out            =param['rows_out'],
        #cols_out            =param['cols_out'],
        #channels_out        =param['channels_out'],
        ports_out           =param['ports_out']
    )

    # top src
    split_layer_top_src = split_layer_top_template_src.format(
        name            =name,
        NAME            =name.upper(),
        buffer_depth=max(param['buffer_depth'],2),
    )

    # write source file
    with open(src_path,'w') as src_file:
        src_file.write(split_layer_src)

    # write top source file
    if not topless:
        top_src_path = os.path.split(src_path)
        top_src_path = os.path.join(top_src_path[0], f'{name}_top.cpp')
        with open(top_src_path,'w') as src_file:
            src_file.write(split_layer_top_src)

    # write header file
    with open(header_path,'w') as header_file:
        header_file.write(split_layer_header)

    return
