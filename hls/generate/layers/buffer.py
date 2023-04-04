# import modules
import os
import shutil

import generate.modules.fork
import generate.modules.buff

buffer_layer_template_header = """//auto generated
#ifndef {NAME}_HPP_
#define {NAME}_HPP_

#include "fork.hpp"
#include "buffer.hpp"

#define name        {name}
#define NAME        {NAME}
#define {NAME}_ID   {id}

typedef b_data_t {name}_data_t;
//typedef b_data_t {name}_ctrl_t;
typedef b_bool_t {name}_ctrl_t;
typedef {name}_data_t {name}_input_t;
typedef {name}_data_t {name}_output_t;

#define {NAME}_BATCH_SIZE   {batch_size}
#define {NAME}_ROWS         {rows}
#define {NAME}_COLS         {cols}
#define {NAME}_CHANNELS     {channels}
#define {NAME}_COARSE       {coarse}
#define {NAME}_DROP_MODE    {drop_mode}

#define {NAME}_COARSE_IN    {NAME}_COARSE
#define {NAME}_COARSE_OUT   {NAME}_COARSE

// FORK
#define {NAME}_FORK_BATCH_SIZE    {batch_size}
#define {NAME}_FORK_ROWS          1
#define {NAME}_FORK_COLS          1
#define {NAME}_FORK_CHANNELS      1 //1 ctrl signal per batch
#define {NAME}_FORK_COARSE        {coarse}
#define {NAME}_FORK_KERNEL_SIZE   1

// BUFFER
#define {NAME}_BUFFER_BATCH_SIZE    {batch_size}
#define {NAME}_BUFFER_ROWS          {rows_out}
#define {NAME}_BUFFER_COLS          {cols_out}
#define {NAME}_BUFFER_CHANNELS      {channels_per_module}
#define {NAME}_BUFFER_DROP_MODE     {drop_mode}


/**
 * FUNCTION DEFINITION
 */

void {name}(
    stream_t({name}_data_t)  in[{NAME}_COARSE],
    stream_t({name}_ctrl_t)  &ctrl_in,
    stream_t({name}_data_t) out[{NAME}_COARSE],
    int mode
);

#undef name
#undef NAME
#endif
"""

buffer_layer_template_src = """//auto generated
#include "{name}.hpp"

void {name}(
    stream_t({name}_data_t)  in[{NAME}_COARSE],
    stream_t({name}_ctrl_t)  &ctrl_in,
    stream_t({name}_data_t) out[{NAME}_COARSE],
    int mode
)
{{

#pragma HLS INLINE OFF
#pragma HLS DATAFLOW

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=ctrl_in
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in  complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0

    stream_t({name}_ctrl_t) fork_out[{NAME}_COARSE];
#pragma HLS STREAM variable=fork_out
#pragma HLS ARRAY_PARTITION variable=fork_out  complete dim=0

{fork}

    for(unsigned int coarseIndex=0;coarseIndex<{NAME}_COARSE;coarseIndex++)
    {{
#pragma HLS UNROLL
{buff}
    }}
}}

"""

buffer_layer_top_template_src = """//auto generated
#include "{name}.hpp"

void {name}_top(
    stream_t({name}_data_t)  in[{NAME}_COARSE],
    stream_t({name}_ctrl_t)  &ctrl_in,
    stream_t({name}_data_t) out[{NAME}_COARSE])
{{

#pragma HLS DATAFLOW

#pragma HLS INTERFACE s_axilite port=return bundle=ctrl
#pragma HLS INTERFACE axis port=in
#pragma HLS INTERFACE axis port=ctrl_in
#pragma HLS INTERFACE axis port=out

#pragma HLS STREAM variable=in
#pragma HLS STREAM variable=ctrl_in
#pragma HLS STREAM variable=out

    int mode=0;
    {name}(in, ctrl_in, out, mode);

}}

"""


def gen_buffer_layer(name,param,src_path,header_path, topless=True):

    #FORK MODULE INIT
    fork = generate.modules.fork.gen_fork_module(
        name+"_fork",
        "ctrl_in",
        "fork_out",
        f"{name}_ctrl_t",
        indent=8
    )

    # BUFFER MODULE INIT
    if param['drop_mode'] == False:
        dm=False
        print("drop mode is false")
    else:
        print("drop mode is true")
        dm=True

    buff = generate.modules.buff.gen_buff_module(
        name+"_buffer",
        "in[coarseIndex]",
        "fork_out[coarseIndex]",
        "out[coarseIndex]",
        f"{name}_data_t",
        drop_mode = dm,
        indent=8
    )

    # src
    buffer_layer_src = buffer_layer_template_src.format(
        name            =name,
        NAME            =name.upper(),
        buffer_depth=max(param['buffer_depth'],2),
        fork            =fork,
        buff            =buff
    )

    if param['drop_mode']:
        dm = 'true'
    else:
        dm = 'false'
    # header
    buffer_layer_header = buffer_layer_template_header.format(
        name                =name,
        NAME                =name.upper(),
        id                  =0, # param['id'],
        batch_size          =param['batch_size'],
        rows                =param['rows_in'],
        cols                =param['cols_in'],
        channels            =param['channels_in'],
        channels_per_module =int(param['channels_in']/(param['coarse_in'])),
        coarse              =param['coarse_in'],
        rows_out            =param['rows_out'],
        cols_out            =param['cols_out'],
        channels_out        =param['channels_out'],
        drop_mode           =dm
    )

    # top src
    buffer_layer_top_src = buffer_layer_top_template_src.format(
        name            =name,
        NAME            =name.upper(),
        buffer_depth=max(param['buffer_depth'],2),
    )

    # write source file
    with open(src_path,'w') as src_file:
        src_file.write(buffer_layer_src)

    # write top source file
    if not topless:
        top_src_path = os.path.split(src_path)
        top_src_path = os.path.join(top_src_path[0], f'{name}_top.cpp')
        with open(top_src_path,'w') as src_file:
            src_file.write(buffer_layer_top_src)

    # write header file
    with open(header_path,'w') as header_file:
        header_file.write(buffer_layer_header)

    return

