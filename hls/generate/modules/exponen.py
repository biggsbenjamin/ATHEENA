exponen_template="""
{indent}exponen<
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
{indent}    {NAME}_CHANNELS,
{indent}    {in_t},
{indent}    {out_t}
{indent}>({input_stream},{output_stream});

"""

def gen_exponen_module(name,input_stream,output_stream,in_type,out_type,indent=0):
    return exponen_template.format(
        NAME            =name.upper(),
        input_stream    =input_stream,
        output_stream   =output_stream,
        in_t            =in_type,
        out_t           =out_type,
        indent          =" "*indent
    )

