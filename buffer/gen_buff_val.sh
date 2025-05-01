#!/bin/bash

#exp_ls='buffer_size1_1 buffer_size1_2 buffer_size1_3 buffer_size1_5 buffer_size1_7 buffer_size1_9 buffer_size1_11 buffer_size1_13'

exp_ls='buffer_size1 buffer_size5 buffer_size7 buffer_size9 buffer_size11 buffer_size13 buffer_size15'
for i in $exp_ls
do
    EXP=${i}
    echo "buffer: $EXP"

    mkdir -p ./impl_val/${EXP}/
    mkdir -p ./impl_val/${EXP}/buffer1/

    # buffer 1 gen - for storing partial fm at early stage
    sbt "run layer conditional_buffer ./data/layers/conditional_buffer/${EXP}/config.json --target-dir=./impl_val/${EXP}/buffer1/ --emission-options=disableMemRandomization,disableRegisterRandomization"
    python scripts/add_attributes.py impl_val/${EXP}/buffer1/ConditionalBufferTop.v impl_val/${EXP}/buffer1/ConditionalBufferTopAttr.v
    vivado -mode batch -source scripts/tcl/generate_ip_package.tcl -tclargs cond_buffer_1_${EXP} impl_val/${EXP}/buffer1/ConditionalBufferTopAttr.v ConditionalBufferTop impl_val/${EXP}/buffer1/

    # get rsc b1
    vivado -mode batch -notrace -source scripts/tcl/get_rsc_usage.tcl -tclargs "_ -part xc7z045ffg900-2 -board xilinx.com:zc706:part0:1.4 -freq 125 -prj-path impl_val/${EXP}/buffer1/ -hw-path impl_val/${EXP}/buffer1/ConditionalBufferTopAttr.v -output-path ./impl_val/${EXP}/buffer1/ -top ConditionalBufferTop"

done
