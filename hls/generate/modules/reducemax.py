reducemax_template="""
{indent}reducemax<
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
{indent}    {NAME}_CHANNELS,
{indent}    {rdmx_t}
{indent}>({input_stream},{output_stream});

"""

def gen_reducemax_module(name,input_stream,output_stream,rdmx_t,indent=0):
    return reducemax_template.format(
        NAME            =name.upper(),
        input_stream    =input_stream,
        output_stream   =output_stream,
        rdmx_t          =rdmx_t,
        indent          =" "*indent
    )

