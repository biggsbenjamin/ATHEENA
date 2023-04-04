# import modules
import os
import shutil
#NOTE doesn't exit atm
#import generate.modules.exit_merge

exit_merge_layer_template_header = """#ifndef {NAME}_HPP_
#define {NAME}_HPP_

#include "buffer.hpp"
#include "exit_merge.hpp"

#define name        {name}
#define NAME        {NAME}
#define {NAME}_ID   {id}

#define {NAME}_BATCH_SIZE               {batch_size}
#define {NAME}_ROWS                     {rows}
#define {NAME}_COLS                     {cols}
#define {NAME}_CHANNELS                 {channels}
#define {NAME}_EXITS                    {ports_in}

// For necessary internal buffering BUFFER
#define {NAME}_BUFFER_BATCH_SIZE        {NAME}_BATCH_SIZE
#define {NAME}_BUFFER_ROWS              {NAME}_ROWS
#define {NAME}_BUFFER_COLS              {NAME}_COLS
#define {NAME}_BUFFER_CHANNELS          {NAME}_CHANNELS

// For EXIT_MERGE
#define {NAME}_EXIT_MERGE_BATCH_SIZE    {NAME}_BATCH_SIZE
#define {NAME}_EXIT_MERGE_ROWS          {NAME}_ROWS
#define {NAME}_EXIT_MERGE_COLS          {NAME}_COLS
#define {NAME}_EXIT_MERGE_CHANNELS      {NAME}_CHANNELS
#define {NAME}_EXIT_MERGE_EXITS         {NAME}_EXITS

typedef b_data_t {name}_data_t;
typedef {name}_data_t {name}_input_t;
typedef {name}_data_t {name}_output_t;

/**
 * FUNCTION DEFINITION
 */

void {name}(
    stream_t({name}_data_t) exits[{NAME}_EXIT_MERGE_EXITS],
    stream_t({name}_data_t) out[1]
);

#undef name
#undef NAME
#endif
"""

exit_merge_layer_template_src = """#include "{name}.hpp"

void {name}(
    stream_t({name}_data_t) exits[{NAME}_EXIT_MERGE_EXITS],
    stream_t({name}_data_t) out[1]
)
{{

#pragma HLS INLINE OFF

#pragma HLS STREAM variable=exits
#pragma HLS STREAM variable=out
#pragma HLS ARRAY_PARTITION variable=exits  complete dim=0

#pragma HLS DATAFLOW

    stream_t({name}_data_t) exits_intr[{NAME}_EXITS];
    #pragma HLS STREAM variable=exits_intr
    const unsigned int exit_num = {NAME}_EXITS;
    // forcing hls to gen fifos for internal streams
    for (int ex=0; ex<exit_num; ex++) {{
        #pragma HLS unroll
        em_buff<
            {NAME}_BUFFER_BATCH_SIZE,
            {NAME}_BUFFER_ROWS,
            {NAME}_BUFFER_COLS,
            {NAME}_BUFFER_CHANNELS,
            {name}_data_t
        >(exits[ex], exits_intr[ex]);
    }}

    exit_merge<
        {NAME}_EXIT_MERGE_BATCH_SIZE,
        {NAME}_EXIT_MERGE_ROWS,
        {NAME}_EXIT_MERGE_COLS,
        {NAME}_EXIT_MERGE_CHANNELS,
        {NAME}_EXIT_MERGE_EXITS,
        {name}_data_t
    >(exits_intr, out[0]);
}}

"""

exit_merge_layer_top_template_src = """//auto generated
#include "{name}.hpp"

void {name}_top(
    stream_t({name}_data_t) exits[{NAME}_EXIT_MERGE_EXITS],
    stream_t({name}_data_t) out[1]
) {{
#pragma HLS DATAFLOW

#pragma HLS INTERFACE s_axilite port=return bundle=ctrl
#pragma HLS INTERFACE axis port=exits
#pragma HLS INTERFACE axis port=out

    {name}(exits, out);

}}

"""

def gen_exit_merge_layer(name,param,src_path,header_path,topless=True):

    # FIXME hardcoding module
    ## EXIT_MERGE MODULE INIT
    #exit_merge = generate.modules.exit_merge.gen_exit_merge_module(
    #    name+"_exit_merge",
    #    "in[coarseIndex]",
    #    "out[coarseIndex]",
    #    exit_merge_t=f"{name}_data_t",
    #    indent=8
    #)

    # src
    exit_merge_layer_src = exit_merge_layer_template_src.format(
        name  =name,
        NAME  =name.upper(),
        buffer_depth=max(param['buffer_depth'],2),
        # FIXME hardcoding module
        #exit_merge  =exit_merge
    )

    # header
    exit_merge_layer_header = exit_merge_layer_template_header.format(
        name                =name,
        NAME                =name.upper(),
        id                  =0, # param['id'],
        batch_size          =param['batch_size'],
        rows                =param['rows_in'],
        cols                =param['cols_in'],
        channels            =param['channels_in'],
        ports_in            =param['ports_in'],
        #channels_per_module =param['channels_in']//param['coarse_in'],
        #coarse              =param['coarse_in'],
        #rows_out            =param['rows_out'],
        #cols_out            =param['cols_out'],
        #channels_out        =param['channels_out'],
        #data_width          =param['data_width'],
        #data_int_width      =param['data_width']//2
    )

    # top src
    exit_merge_layer_top_src = exit_merge_layer_top_template_src.format(
        name  =name,
        NAME  =name.upper(),
        buffer_depth=max(param['buffer_depth'],2),
    )

    # write source file
    with open(src_path,'w') as src_file:
        src_file.write(exit_merge_layer_src)

    if not topless:
        # write top source file
        top_src_path = os.path.split(src_path)
        top_src_path = os.path.join(top_src_path[0], f'{name}_top.cpp')
        with open(top_src_path,'w') as src_file:
            src_file.write(exit_merge_layer_top_src)

    # write header file
    with open(header_path,'w') as header_file:
        header_file.write(exit_merge_layer_header)

    return
