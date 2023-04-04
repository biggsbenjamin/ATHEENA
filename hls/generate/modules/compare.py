compare_template="""
{indent}compare<
{indent}    {NAME}_BATCH_SIZE,
{indent}    {in_t},
{indent}    {out_t}
{indent}>({input_max},{input_thr},{threshold},{output_stream});

"""

def gen_compare_module(name,
        input_max,
        input_thr,
        threshold,
        output_stream,
        in_t,out_t,
        indent=0):
    return compare_template.format(
        NAME            =name.upper(),
        input_max       =input_max,
        input_thr       =input_thr,
        threshold       =threshold,
        output_stream   =output_stream,
        in_t            =in_t,
        out_t           =out_t,
        indent          =" "*indent
    )


