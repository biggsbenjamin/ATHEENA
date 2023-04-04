bias_template = """
//auto generated
{indent}bias<
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
{indent}    {NAME}_FILTERS,
{indent}    {data_t},
{indent}    {biases_t}
{indent}>({input_stream},{biases_stream},{output_stream});

"""

def gen_bias_module(name,input_stream,biases_stream,output_stream,
        data_t="data_t",biases_t="biases_t",indent=0):
    return bias_template.format(
        NAME            =name.upper(),
        input_stream    =input_stream,
        biases_stream   =biases_stream,
        output_stream   =output_stream,
        data_t          =data_t,
        biases_t        =biases_t,
        indent          =" "*indent
    )
