fork_template="""
{indent}fork<
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
{indent}    {NAME}_CHANNELS,
{indent}    {NAME}_COARSE,
#if {NAME}_KERNEL_SIZE_X > 1 || {NAME}_KERNEL_SIZE_Y > 1
{indent}    {NAME}_KERNEL_SIZE_X,
{indent}    {NAME}_KERNEL_SIZE_Y,
#endif
{indent}    {fork_t}
{indent}>({input_stream},{output_stream});
"""
#fork_fp_template="""
#{indent}fork<
#{indent}    {NAME}_BATCH_SIZE,
#{indent}    {NAME}_ROWS,
#{indent}    {NAME}_COLS,
#{indent}    {NAME}_CHANNELS,
#{indent}    {NAME}_COARSE,
##if {NAME}_KERNEL_SIZE_X > 1 || {NAME}_KERNEL_SIZE_Y > 1
#{indent}    {NAME}_KERNEL_SIZE_X,
#{indent}    {NAME}_KERNEL_SIZE_Y,
##endif
#{indent}    {fork_t},
#{indent}    true
#{indent}>({input_stream},{output_stream});
#
#"""

def gen_fork_module(name,input_stream,output_stream,
        fork_t="data_t",indent=0, fp_fork=False):
    #if fp_fork:
    #    return fork_fp_template.format(
    #        NAME            =name.upper(),
    #        input_stream    =input_stream,
    #        output_stream   =output_stream,
    #        fork_t          =fork_t,
    #        indent          =" "*indent
    #    )
    return fork_template.format(
        NAME            =name.upper(),
        input_stream    =input_stream,
        output_stream   =output_stream,
        fork_t          =fork_t,
        indent          =" "*indent,
    )
