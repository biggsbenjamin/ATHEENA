# import modules
import os
import shutil

import generate.modules.sliding_window
import generate.modules.fork
import generate.modules.conv
import generate.modules.accum
import generate.modules.glue
import generate.modules.bias

convolution_layer_template_header = """//auto generated file
#ifndef {NAME}_HPP_
#define {NAME}_HPP_

#include "sliding_window.hpp"
#include "fork.hpp"
#include "conv.hpp"
#include "accum.hpp"
#include "glue.hpp"
#include "bias.hpp"

#define name        {name}
#define NAME        {NAME}
#define {NAME}_ID   {id}

// parameters
#define {NAME}_BATCH_SIZE    {batch_size}
#define {NAME}_ROWS          {rows}
#define {NAME}_COLS          {cols}
#define {NAME}_CHANNELS      {channels}
#define {NAME}_FILTERS       {filters}
#define {NAME}_GROUPS        {groups}
#define {NAME}_COARSE_IN     {coarse_in}
#define {NAME}_COARSE_OUT    {coarse_out}
#define {NAME}_COARSE_GROUP  {coarse_group}
#define {NAME}_KERNEL_SIZE_X {kernel_size_x}
#define {NAME}_KERNEL_SIZE_Y {kernel_size_y}
#define {NAME}_FINE          {fine}
#define {NAME}_STRIDE_X      {stride_x}
#define {NAME}_STRIDE_Y      {stride_y}
#define {NAME}_HAS_BIAS      {has_bias}
#define {NAME}_WR_FACTOR     {wr_factor}

// coefficients
#define {NAME}_WEIGHTS {NAME}_FILTERS*DIVIDE({NAME}_CHANNELS,{NAME}_GROUPS)*{NAME}_KERNEL_SIZE_X*{NAME}_KERNEL_SIZE_Y
#define {NAME}_BIASES  {NAME}_FILTERS

// dimensions out
#define {NAME}_ROWS_OUT     {rows_out}
#define {NAME}_COLS_OUT     {cols_out}
#define {NAME}_CHANNELS_OUT {channels_out}

// define data types
//typedef ap_fixed<{input_width},{input_int_width},AP_RND>    {name}_input_t;
//typedef ap_fixed<{output_width},{output_int_width},AP_RND>  {name}_output_t;
//typedef ap_fixed<{acc_width},{acc_int_width},AP_RND>        {name}_acc_t;
//typedef ap_fixed<{weight_width},{weight_int_width},AP_RND>  {name}_weight_t;
//typedef ap_fixed<{biases_width},{biases_int_width},AP_RND>  {name}_biases_t;
// forcing common data types
typedef b_data_t    {name}_input_t;
typedef b_data_t    {name}_output_t;
typedef b_acc_t     {name}_acc_t;
typedef weight_t    {name}_weight_t;
typedef weight_t    {name}_biases_t;

// SLIDING WINDOW
#define {NAME}_SLIDING_WINDOW_BATCH_SIZE    {batch_size}
#define {NAME}_SLIDING_WINDOW_ROWS          {rows}
#define {NAME}_SLIDING_WINDOW_COLS          {cols}
#define {NAME}_SLIDING_WINDOW_CHANNELS      {channels_per_module}
#define {NAME}_SLIDING_WINDOW_KERNEL_SIZE_X {kernel_size_x}
#define {NAME}_SLIDING_WINDOW_KERNEL_SIZE_Y {kernel_size_y}
#define {NAME}_SLIDING_WINDOW_STRIDE_X      {stride_x}
#define {NAME}_SLIDING_WINDOW_STRIDE_Y      {stride_y}
#define {NAME}_SLIDING_WINDOW_PAD_LEFT      {pad_left}
#define {NAME}_SLIDING_WINDOW_PAD_RIGHT     {pad_right}
#define {NAME}_SLIDING_WINDOW_PAD_TOP       {pad_top}
#define {NAME}_SLIDING_WINDOW_PAD_BOTTOM    {pad_bottom}

// FORK
#define {NAME}_FORK_BATCH_SIZE    {batch_size}
#define {NAME}_FORK_ROWS          {rows_out}
#define {NAME}_FORK_COLS          {cols_out}
#define {NAME}_FORK_CHANNELS      {channels_per_module}
#define {NAME}_FORK_COARSE        {coarse_out}
#define {NAME}_FORK_KERNEL_SIZE_X {kernel_size_x}
#define {NAME}_FORK_KERNEL_SIZE_Y {kernel_size_y}

// CONV
#define {NAME}_CONV_BATCH_SIZE    {batch_size}
#define {NAME}_CONV_ROWS          {rows_out}
#define {NAME}_CONV_COLS          {cols_out}
#define {NAME}_CONV_GROUPS        {groups_per_module}
#define {NAME}_CONV_CHANNELS      {channels_per_module}
#define {NAME}_CONV_FILTERS       {filters_per_module}
#define {NAME}_CONV_KERNEL_SIZE_X {kernel_size_x}
#define {NAME}_CONV_KERNEL_SIZE_Y {kernel_size_y}
#define {NAME}_CONV_FINE          {fine}
#define {NAME}_CONV_INTERVAL      {interval}
// Vivado template work around
#define {NAME}_CONV_CHANNELS_PER_GROUP  {channels_per_module_per_group}
#define {NAME}_CONV_FILTERS_PER_GROUP   {filters_per_module_per_group}

// ACCUM
#define {NAME}_ACCUM_BATCH_SIZE         {batch_size}
#define {NAME}_ACCUM_ROWS               {rows_out}
#define {NAME}_ACCUM_COLS               {cols_out}
#define {NAME}_ACCUM_GROUPS             {groups_per_module}
#define {NAME}_ACCUM_CHANNELS           {channels_per_module}
#define {NAME}_ACCUM_FILTERS            {filters_per_module}
// Vivado template workaround
#define {NAME}_ACCUM_CHANNELS_PER_GROUP  {channels_per_module_per_group}
#define {NAME}_ACCUM_FILTERS_PER_GROUP   {filters_per_module_per_group}

// GLUE
#define {NAME}_GLUE_BATCH_SIZE   {batch_size}
#define {NAME}_GLUE_ROWS         {rows_out}
#define {NAME}_GLUE_COLS         {cols_out}
#define {NAME}_GLUE_FILTERS      {channels_out}
#define {NAME}_GLUE_COARSE_IN    {coarse_in}
#define {NAME}_GLUE_COARSE_OUT   {coarse_out}
#define {NAME}_GLUE_COARSE_GROUP {coarse_group}

// BIAS
#define {NAME}_BIAS_BATCH_SIZE   {batch_size}
#define {NAME}_BIAS_ROWS         {rows_out}
#define {NAME}_BIAS_COLS         {cols_out}
#define {NAME}_BIAS_FILTERS      DIVIDE({NAME}_FILTERS,{NAME}_COARSE_OUT*{NAME}_WR_FACTOR)

/**
 * FUNCTION DEFINITION
 */

void {name}(
    const {name}_weight_t weights[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP][{NAME}_COARSE_OUT][DIVIDE({NAME}_WEIGHTS,{NAME}_COARSE_IN*{NAME}_COARSE_GROUP*{NAME}_COARSE_OUT*{NAME}_KERNEL_SIZE_X*{NAME}_KERNEL_SIZE_Y)][{NAME}_KERNEL_SIZE_X][{NAME}_KERNEL_SIZE_Y],
#if ({NAME}_HAS_BIAS == 1)
    const {name}_biases_t biases[{NAME}_COARSE_OUT][DIVIDE({NAME}_FILTERS,{NAME}_COARSE_OUT*{NAME}_WR_FACTOR)],
#endif
    stream_t({name}_input_t)  in[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP],
    stream_t({name}_output_t) out[{NAME}_COARSE_OUT*{NAME}_COARSE_GROUP],
    int mode
);

#undef name
#undef NAME
#endif
"""

convolution_layer_template_src = """//auto generated file
#include "{name}.hpp"

void {name}(
    const {name}_weight_t weights[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP][{NAME}_COARSE_OUT][DIVIDE({NAME}_WEIGHTS,{NAME}_COARSE_IN*{NAME}_COARSE_GROUP*{NAME}_COARSE_OUT*{NAME}_KERNEL_SIZE_X*{NAME}_KERNEL_SIZE_Y)][{NAME}_KERNEL_SIZE_X][{NAME}_KERNEL_SIZE_Y],
#if ({NAME}_HAS_BIAS == 1)
    const {name}_biases_t biases[{NAME}_COARSE_OUT][DIVIDE({NAME}_FILTERS,{NAME}_COARSE_OUT*{NAME}_WR_FACTOR)],
#endif
    stream_t({name}_input_t)  in[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP],
    stream_t({name}_output_t) out[{NAME}_COARSE_OUT*{NAME}_COARSE_GROUP],
    int mode
)
{{

//#pragma HLS INLINE OFF

#pragma HLS STREAM variable=in //depth={buffer_depth}
#pragma HLS STREAM variable=out

#pragma HLS ARRAY_PARTITION variable=in  complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0

#pragma HLS DATAFLOW
//#pragma HLS stable variable=weights

    {streams}

    for(unsigned int i=0;i<{NAME}_COARSE_IN*{NAME}_COARSE_GROUP;i++) {{
        #pragma HLS unroll

        {sliding_window}
        {fork}

        for(unsigned int j=0;j<{NAME}_COARSE_OUT;j++) {{
            #pragma HLS unroll

            {conv}
            {accum}

        }}
    }}

    {glue}
#if ({NAME}_HAS_BIAS == 1)
    for(unsigned int j=0;j<{NAME}_COARSE_OUT;j++) {{
        #pragma HLS unroll
        {bias}
    }}
#endif
}}

"""

convolution_layer_top_template_src = """//auto generated
#include "{name}.hpp"

{weights}
{biases}

void {name}_top(
    stream_t({name}_input_t)  in[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP],
    stream_t({name}_output_t) out[{NAME}_COARSE_OUT*{NAME}_COARSE_GROUP]
)
{{

#pragma HLS DATAFLOW

#pragma HLS INTERFACE s_axilite port=return                     bundle=ctrl
#pragma HLS INTERFACE axis port=in
#pragma HLS INTERFACE axis port=out

#pragma HLS STREAM variable=in //depth={buffer_depth}
#pragma HLS STREAM variable=out

{weights_init}
{biases_init}

    int mode=0;

    {name}({name}_weights,
#if ({NAME}_HAS_BIAS == 1)
        {name}_biases,
#endif
        in,out,mode);

}}

"""


def gen_convolution_layer(name,param,src_path,header_path,topless=True,wr_factor=1):

    # get sliding window type
    single_channel  = True if param['channels_in'] == 1 else False
    single_stream   = True if param['kernel_size'][0] == 1 and param['kernel_size'][1] == 1 else False
    depthwise       = True if ((param['groups'] == param['filters']) and (param['groups'] == param['channels_in'])) else False
    grouped         = True if param['groups'] > 1 else False
    has_bias        = True if param['has_bias'] ==1 else False

    inputs = {
        'sliding_window': "in[i]",
        'fork'          : "sw_out[i]",
        'conv'          : "fork_out[i][j]",
        'accum'         : "conv_out[i][j]",
        'glue'          : "accum_out",
        'bias'          : "glue_out[j]"
    }
    outputs = {
        'sliding_window': "sw_out[i]",
        'fork'          : "fork_out[i]",
        'conv'          : "conv_out[i][j]",
        'accum'         : "accum_out[i][j]",
        'glue'          : "glue_out",
        'bias'          : "out[j]"
    }

    if single_stream:
        inputs['fork'] = "in[i]"
        inputs.pop('sliding_window',None)
        outputs.pop('sliding_window',None)

    if single_channel:
        inputs['glue'] = "conv_out"
        #outputs['conv'] = "out[j]"
        inputs.pop('accum',None)
        outputs.pop('accum',None)
        #inputs.pop('glue',None)
        #outputs.pop('glue',None)

    if not has_bias:
        inputs.pop('bias',None)
        outputs.pop('bias',None)
        outputs['glue'] = "out"

    streams = ""

    # SLIDING WINDOW MODULE INIT
    if 'sliding_window' in inputs:
        streams += """
    stream_t({name}_input_t) sw_out[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP][{NAME}_KERNEL_SIZE_X][{NAME}_KERNEL_SIZE_Y];
    #pragma HLS STREAM variable=sw_out
    #pragma HLS ARRAY_PARTITION variable=sw_out complete dim=0
        """.format(NAME=name.upper(),name=name)
        sliding_window = generate.modules.sliding_window.gen_sliding_window_module(
            name+"_sliding_window",
            inputs['sliding_window'],
            outputs['sliding_window'],
            sliding_window_t=f"{name}_input_t",
            indent=8
        )
    else:
        sliding_window = ''

    # FORK MODULE INIT
    if 'fork' in inputs:
        streams += """
    stream_t({name}_input_t) fork_out[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP][{NAME}_COARSE_OUT]{single_stream}[{NAME}_KERNEL_SIZE_X][{NAME}_KERNEL_SIZE_Y];
    #pragma HLS STREAM variable=fork_out
    #pragma HLS ARRAY_PARTITION variable=fork_out complete dim=0
        """.format(NAME=name.upper(),name=name,
                single_stream=";//" if single_stream else "")
        fork = generate.modules.fork.gen_fork_module(
            name+"_fork",
            inputs['fork'],
            outputs['fork'],
            fork_t=f"{name}_input_t",
            indent=8
        )
    else:
        fork = ''

    # CONV MODULE INIT
    if 'conv' in inputs:
        streams += """
    stream_t({name}_acc_t) conv_out[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP][{NAME}_COARSE_OUT];
    #pragma HLS STREAM variable=conv_out
    #pragma HLS ARRAY_PARTITION variable=conv_out complete dim=0
        """.format(NAME=name.upper(),name=name)
        conv = generate.modules.conv.gen_conv_module(
            name+"_conv",
            param, #NOTE PROVIDE PARAMS FOR LESS MESSY TEMPLATING
            inputs['conv'],
            "weights[i][j]",
            outputs['conv'],
            data_t=f"{name}_input_t",
            acc_t=f"{name}_acc_t",
            weight_t=f"{name}_weight_t",
            indent=12
        )
    else:
        conv = ''

    # ACCUM MODULE INIT
    if 'accum' in inputs:
        streams += """
    stream_t({name}_acc_t) accum_out[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP][{NAME}_COARSE_OUT];
    #pragma HLS STREAM variable=accum_out
    #pragma HLS ARRAY_PARTITION variable=accum_out complete dim=0
        """.format(NAME=name.upper(),name=name)
        accum = generate.modules.accum.gen_accum_module(
            name+"_accum",
            param,
            inputs['accum'],
            outputs['accum'],
            accum_t=f"{name}_acc_t",
            indent=12
        )
    else:
        accum = ''

    # GLUE MODULE INIT
    if 'glue' in inputs:
        glue = generate.modules.glue.gen_glue_module(
            name+"_glue",
            inputs['glue'],
            outputs['glue'],
            acc_t=f"{name}_acc_t",
            data_t=f"{name}_output_t",
            indent=4
        )
    else:
        glue = ''

    # BIAS MODULE INIT
    if 'bias' in inputs:
        # add output for glue module to feed into bias module
        streams += """
    stream_t({name}_output_t) glue_out[{NAME}_COARSE_OUT];
    #pragma HLS STREAM variable=glue_out
    #pragma HLS ARRAY_PARTITION variable=glue_out complete dim=0
        """.format(NAME=name.upper(),name=name)
        bias = generate.modules.bias.gen_bias_module(
            name+"_bias",
            inputs['bias'],
            "biases[j]",
            outputs['bias'],
            data_t=f"{name}_output_t",
            biases_t=f"{name}_biases_t",
            indent=8
        )
    else:
        bias = ''

    # src
    convolution_layer_src = convolution_layer_template_src.format(
        name            =name,
        NAME            =name.upper(),
        buffer_depth    =max(param['buffer_depth'],2),
        streams         =streams,
        sliding_window  =sliding_window,
        fork            =fork,
        conv            =conv,
        accum           =accum,
        glue            =glue,
        bias            =bias
    )

    # header
    convolution_layer_header = convolution_layer_template_header.format(
        name                =name,
        NAME                =name.upper(),
        id                  =0, # param['id'],
        batch_size          =param['batch_size'],
        rows                =param['rows_in'],
        cols                =param['cols_in'],
        channels            =param['channels_in'],
        channels_per_module =param['channels_in']//(param['coarse_in']*param['coarse_group']),
        channels_per_module_per_group =param['channels_in']//(param['coarse_in']*param['coarse_group']*param["groups"]),
        filters             =param['filters'],
        filters_per_module  =param['filters']//(param['coarse_out']*param['coarse_group']),
        filters_per_module_per_group =param['filters']//(param['coarse_out']*param['coarse_group']*param["groups"]),
        groups              =param['groups'],
        groups_per_module   =param['groups']//param['coarse_group'],
        coarse_in           =param['coarse_in'],
        coarse_out          =param['coarse_out'],
        coarse_group        =param['coarse_group'],
        fine                =param['fine'],
        interval            =(param['kernel_size'][0]*param['kernel_size'][1])//param['fine'],
        kernel_size_x       =param['kernel_size'][0],
        kernel_size_y       =param['kernel_size'][1],
        stride_x            =param['stride'][0],
        stride_y            =param['stride'][1],
        pad_left            =param['pad_left'],
        pad_right           =param['pad_right'],
        pad_top             =param['pad_top'],
        pad_bottom          =param['pad_bottom'],
        rows_out            =param['rows_out'],
        cols_out            =param['cols_out'],
        channels_out        =param['channels_out'],
        input_width         =param['input_width'],
        input_int_width     =param['input_width']//2,
        output_width        =param['output_width'],
        output_int_width    =param['output_width']//2,
        acc_width           =param['acc_width'],
        acc_int_width       =param['acc_width']//2,
        weight_width        =param['weight_width'],
        weight_int_width    =param['weight_width']//2,
        has_bias            =param['has_bias'],
        biases_width        =param['biases_width'],
        biases_int_width    =param['biases_width']//2,
        wr_factor           =wr_factor
    )

    ############ including weights in top file ##############

    weights = str(generate_weight_def(
        name,
        kernel_size_x=int(param["kernel_size"][0]),
        kernel_size_y=int(param["kernel_size"][1]),
        wr=False
    ))
    weights_init = str(generate_weight_init(
        name,
        wr=False
    ))
    biases=''
    biases_init=''
    if has_bias:
        biases += generate_bias_def(name)
        biases_init += generate_bias_init(name)

    # top src
    convolution_layer_top_src = convolution_layer_top_template_src.format(
        name            =name,
        NAME            =name.upper(),
        buffer_depth    =max(param['buffer_depth'],2),
        weights=weights,
        weights_init=weights_init,
        biases=biases,
        biases_init=biases_init,
    )

    # write source file
    with open(src_path,'w') as src_file:
        src_file.write(convolution_layer_src)

    # write top source file
    if not topless:
        top_src_path = os.path.split(src_path)
        top_src_path = os.path.join(top_src_path[0], f'{name}_top.cpp')
        with open(top_src_path,'w') as src_file:
            src_file.write(convolution_layer_top_src)

    # write header file
    with open(header_path,'w') as header_file:
        header_file.write(convolution_layer_header)

    return



######################## copied from partition.py ####################

class generate_weight_def:
    # initialise class
    def __init__(self, name, kernel_size_x=1, kernel_size_y=1, wr=False):
        self.name       = name
        self.type       = "static" if wr else "const static"
        self.kernel_dim = "[{NAME}_KERNEL_SIZE_X][{NAME}_KERNEL_SIZE_Y]".format(NAME=self.name.upper())

    def __str__(self):
        return """
{type} {name}_weight_t {name}_weights[{NAME}_COARSE_IN*{NAME}_COARSE_GROUP][{NAME}_COARSE_OUT][DIVIDE({NAME}_WEIGHTS,{NAME}_COARSE_IN*{NAME}_COARSE_GROUP*{NAME}_COARSE_OUT*{NAME}_KERNEL_SIZE_X*{NAME}_KERNEL_SIZE_Y)]{kernel_dim} = {{
#include "{name}_weights_0.csv"
}};
""".format(
        NAME=self.name.upper(),
        name=self.name,
        type=self.type,
        kernel_dim=self.kernel_dim
    )

# class for weight initialisation
class generate_weight_init():
    # initialise class
    def __init__(self, name, wr=False):
        self.name = name
        self.bram_type = "RAM" if wr else "ROM"
        #FIXME core resource specification gets errors

    def __str__(self):
        return """
#pragma HLS ARRAY_PARTITION variable={name}_weights complete dim=1
#pragma HLS ARRAY_PARTITION variable={name}_weights complete dim=2
#pragma HLS RESOURCE variable={name}_weights //core={bram_type}
//#pragma HLS STREAM variable={name}_weights off
#pragma HLS STABLE variable={name}_weights

""".format(name=self.name,bram_type=self.bram_type)

######## Generating biases #########
def generate_bias_def(name):
    div = "{NAME}_COARSE_OUT".format(NAME=name.upper())
    return """
const static {name}_biases_t {name}_biases[{NAME}_COARSE_OUT][DIVIDE({NAME}_FILTERS,{div})] = {{
#include "{name}_biases.csv"
}};
""".format(NAME=name.upper(), name=name, div=div)

def generate_bias_init(name):
    #FIXME core resource specification gets errors
    bi = """
#pragma HLS ARRAY_PARTITION variable={name}_biases complete dim=1
#pragma HLS RESOURCE variable={name}_biases //core=ROM
#pragma HLS STABLE variable={name}_biases
""".format(name=name)
    return bi
