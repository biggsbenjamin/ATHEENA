softmax_sum_template="""
{indent}softmax_sum<
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
{indent}    {NAME}_CHANNELS,
{indent}    {sfmsm_t}
{indent}>({input_stream},{output_stream});

"""

def gen_softmax_sum_module(name,input_stream,output_stream,sfmsm_t,indent=0):
    return softmax_sum_template.format(
        NAME            =name.upper(),
        input_stream    =input_stream,
        output_stream   =output_stream,
        sfmsm_t         =sfmsm_t,
        indent          =" "*indent
    )


