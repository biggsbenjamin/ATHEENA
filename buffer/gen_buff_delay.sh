#!/bin/bash

# 16, 25, 51, 102, 204, 406 (for 1280 fm size, crs 1)
#exp_ls='buffer_20480_delay buffer_32000_delay buffer_65280_delay buffer_130560_delay'
exp_ls='buffer_261120_delay buffer_523520_delay'
for i in $exp_ls
do
    EXP=${i}
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
