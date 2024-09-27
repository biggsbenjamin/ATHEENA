#!/bin/bash

#EXP=hw_buffer_exp_48
#EXP=hw_buffer_exp_64
#EXP=hw_buffer_exp_128
#EXP=hw_buffer_exp_22
#EXP=hw_buffer_exp_18
#EXP=hw_buffer_exp_20
#EXP=hw_buffer_exp_16

for i in {24..26..2}
do
    EXP=hw_buffer_exp_${i}
    echo "buffer: $EXP"

    mkdir -p ./impl/${EXP}/
    mkdir -p ./impl/${EXP}/buffer1/

    # buffer 1 gen - for storing partial fm at early stage
    sbt "run layer conditional_buffer ./data/layers/conditional_buffer/${EXP}/config.json --target-dir=./impl/${EXP}/buffer1/ --emission-options=disableMemRandomization,disableRegisterRandomization"
    python scripts/add_attributes.py impl/${EXP}/buffer1/ConditionalBufferTop.v impl/${EXP}/buffer1/ConditionalBufferTopAttr.v
    vivado -mode batch -source scripts/tcl/generate_ip_package.tcl -tclargs cond_buffer_1_${EXP} impl/${EXP}/buffer1/ConditionalBufferTopAttr.v ConditionalBufferTop impl/${EXP}/buffer1/

    # get rsc b1
    vivado -mode batch -notrace -source scripts/tcl/get_rsc_usage.tcl -tclargs "_ -part xc7z045ffg900-2 -board xilinx.com:zc706:part0:1.4 -freq 125 -prj-path impl/${EXP}/buffer1/ -hw-path impl/${EXP}/buffer1/ConditionalBufferTopAttr.v -output-path ./impl/${EXP}/buffer1/ -top ConditionalBufferTop"

done
