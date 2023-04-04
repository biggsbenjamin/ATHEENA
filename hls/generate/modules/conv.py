conv_start          ="{indent}conv<\n"
conv_iter="""
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
"""
conv_ch             ="{indent}    {NAME}_CHANNELS,\n"
conv_fil            ="{indent}    {NAME}_FILTERS,\n"
conv_grp            ="{indent}    {NAME}_GROUPS,\n"
conv_chPerGrp       ="{indent}    {NAME}_CHANNELS_PER_GROUP,\n"
conv_filPerGrp      ="{indent}    {NAME}_FILTERS_PER_GROUP,\n"
conv_kernel="""
{indent}    {NAME}_FINE,
{indent}    {NAME}_KERNEL_SIZE_X,
{indent}    {NAME}_KERNEL_SIZE_Y,
"""
conv_types="""
{indent}    {data_t},
{indent}    {weight_t},
{indent}    {acc_t}
"""
conv_hack           ="{indent}    ,{acc_t}\n"
conv_end            ="{indent}>({input_stream},{weights_stream},{output_stream});\n"


def gen_conv_module(name, param,input_stream,weights_stream,output_stream,
        data_t="data_t",weight_t="weight_t",acc_t="acc_t",indent=0):

    conv_template=conv_start
    # bunch of if statements for what to include
    if param['rows_out']*param['cols_out']*param['batch_size'] > 1:
        conv_template+=conv_iter
    conv_template+=conv_ch
    if param['filters']//(param['coarse_out']*param['coarse_group']) > 1:
        conv_template+=conv_fil
    conv_template+=conv_grp
    if param['channels_in']//(param['coarse_in']*param['coarse_group']*param["groups"]) > 1:
        conv_template+=conv_chPerGrp
    if param['filters']//(param['coarse_out']*param['coarse_group']*param["groups"]) > 1:
        conv_template+=conv_filPerGrp
    if param['kernel_size'][0] > 1 or param['kernel_size'][1] > 1:
        conv_template+=conv_kernel
    conv_template+=conv_types
    if param['filters']//(param['coarse_out']*param['coarse_group']) == 1 and \
            param['channels_in']//(param['coarse_in']*param['coarse_group']*param["groups"]) == 1:
        conv_template+=conv_hack
    conv_template+=conv_end

    return conv_template.format(
        NAME            =name.upper(),
        input_stream    =input_stream,
        weights_stream  =weights_stream,
        output_stream   =output_stream,
        data_t          =data_t,
        weight_t        =weight_t,
        acc_t           =acc_t,
        indent          =" "*indent
    )
