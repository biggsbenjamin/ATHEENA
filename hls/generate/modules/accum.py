accum_start     ="{indent}accum<\n"
accum_iter      ="""
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
"""
accum_chFil     ="""
{indent}    {NAME}_CHANNELS,
{indent}    {NAME}_FILTERS,
"""
accum_filPerGrp ="{indent}    {NAME}_FILTERS_PER_GROUP,\n"
accum_grp       ="{indent}    {NAME}_GROUPS,\n"
accum_end       ="""
{indent}    {accum_t}
{indent}>({input_stream},{output_stream});
"""

def gen_accum_module(name,param,input_stream,output_stream,
        accum_t="data_t",indent=0):
    accum_template=accum_start
    if param['rows_out']*param['cols_out']*param['batch_size'] > 1:
        accum_template+=accum_iter
    accum_template+=accum_chFil
    if param['filters']//(param['coarse_out']*param['coarse_group']*param["groups"]) > 1:
        accum_template+=accum_filPerGrp
    if param['rows_out']*param['cols_out']*param['batch_size'] > 1:
        accum_template+=accum_grp
    accum_template+=accum_end

    return accum_template.format(
        NAME            =name.upper(),
        input_stream    =input_stream,
        output_stream   =output_stream,
        accum_t         =accum_t,
        indent          =" "*indent
    )
