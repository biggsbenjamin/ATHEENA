buff_big_template="""
{indent}buffer_big<
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
{indent}    {NAME}_CHANNELS,
{indent}    {NAME}_DROP_MODE,
{indent}    {buff_t}
{indent}>({input_stream}, {ctrl_input_stream}, {output_stream});

"""

buff_template="""
{indent}buffer<
{indent}    {NAME}_BATCH_SIZE,
{indent}    {NAME}_ROWS,
{indent}    {NAME}_COLS,
{indent}    {NAME}_CHANNELS,
{indent}    {NAME}_DROP_MODE,
{indent}    {buff_t}
{indent}>({input_stream}, {ctrl_input_stream}, {output_stream});

"""

def gen_buff_module(name,input_stream, ctrl_input_stream,output_stream,
        buff_type, drop_mode=False,indent=0):
    if drop_mode:
        print("drop mode is true - using rsc intense version")
        return buff_big_template.format(
            NAME                =name.upper(),
            input_stream        =input_stream,
            ctrl_input_stream   =ctrl_input_stream,
            output_stream       =output_stream,
            buff_t              =buff_type,
            indent              =" "*indent
        )
    else:
        print("drop mode is false - using rsc save version (normal)")
        return buff_template.format(
            NAME                =name.upper(),
            input_stream        =input_stream,
            ctrl_input_stream   =ctrl_input_stream,
            output_stream       =output_stream,
            buff_t              =buff_type,
            indent              =" "*indent
        )


