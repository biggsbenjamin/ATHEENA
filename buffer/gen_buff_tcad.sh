#!/bin/bash

#EXP=tcad_buff_1
#EXP=tcad_buff_3
#EXP=tcad_buff_12
exp_ls='tcad_buff_1 tcad_buff_3 tcad_buff_12'
for i in $exp_ls
do
    EXP=${i}
    echo "buffer: $EXP"

    mkdir -p ./impl_tcad/${EXP}/
    mkdir -p ./impl_tcad/${EXP}/buffer1/

    # buffer 1 gen - for storing partial fm at early stage
    sbt "run layer conditional_buffer ./data/layers/conditional_buffer/${EXP}/config.json --target-dir=./impl_tcad/${EXP}/buffer1/ --emission-options=disableMemRandomization,disableRegisterRandomization"
    python scripts/add_attributes.py impl_tcad/${EXP}/buffer1/ConditionalBufferTop.v impl_tcad/${EXP}/buffer1/ConditionalBufferTopAttr.v
    vivado -mode batch -source scripts/tcl/generate_ip_package.tcl -tclargs cond_buffer_1_${EXP} impl_tcad/${EXP}/buffer1/ConditionalBufferTopAttr.v ConditionalBufferTop impl_tcad/${EXP}/buffer1/

    # get rsc b1
    vivado -mode batch -notrace -source scripts/tcl/get_rsc_usage.tcl -tclargs "_ -part xc7z045ffg900-2 -board xilinx.com:zc706:part0:1.4 -freq 125 -prj-path impl_tcad/${EXP}/buffer1/ -hw-path impl_tcad/${EXP}/buffer1/ConditionalBufferTopAttr.v -output-path ./impl_tcad/${EXP}/buffer1/ -top ConditionalBufferTop"

done
