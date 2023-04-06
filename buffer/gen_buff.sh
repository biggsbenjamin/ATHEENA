#!/bin/bash

list="30 40 50 60 70 80 90 95"
echo "Specify resource limit to generate: 30,40,50,60,70,80,90,95?"
read test_rsc

if [[ $list =~ (^|[[:space:]])$test_rsc($|[[:space:]]) ]]
    then
        echo "Valid rsc"
    else
        echo "Invalid rsc"
        exit
fi

#test_rsc=95

mkdir ./impl/CONF_ee_${test_rsc}rsc-buffers/
mkdir ./impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/
mkdir ./impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/

# buffer 0 gen - storing EE result
# gnerate the verilog from the chisel template
sbt "run layer conditional_buffer ./data/layers/conditional_buffer/test_${test_rsc}0/config.json --target-dir=./impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/ --emission-options=disableMemRandomization,disableRegisterRandomization"
# specify bram usage
python scripts/add_attributes.py impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/ConditionalBufferTop.v impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/ConditionalBufferTopAttr.v
# generate ip for buffer
vivado -mode batch -source scripts/tcl/generate_ip_package.tcl -tclargs cond_buffer_0_${test_rsc} impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/ConditionalBufferTopAttr.v ConditionalBufferTop impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/

# buffer 1 gen - for storing partial fm at early stage
sbt "run layer conditional_buffer ./data/layers/conditional_buffer/test_${test_rsc}1/config.json --target-dir=./impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/ --emission-options=disableMemRandomization,disableRegisterRandomization"
python scripts/add_attributes.py impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/ConditionalBufferTop.v impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/ConditionalBufferTopAttr.v
vivado -mode batch -source scripts/tcl/generate_ip_package.tcl -tclargs cond_buffer_1_${test_rsc} impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/ConditionalBufferTopAttr.v ConditionalBufferTop impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/

# get rsc b0
vivado -mode batch -notrace -source scripts/tcl/get_rsc_usage.tcl -tclargs "_ -part xc7z045ffg900-2 -board xilinx.com:zc706:part0:1.4 -freq 125 -prj-path impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/ -hw-path impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/ConditionalBufferTopAttr.v -output-path ./impl/CONF_ee_${test_rsc}rsc-buffers/buffer0/ -top ConditionalBufferTop"

# get rsc b1
vivado -mode batch -notrace -source scripts/tcl/get_rsc_usage.tcl -tclargs "_ -part xc7z045ffg900-2 -board xilinx.com:zc706:part0:1.4 -freq 125 -prj-path impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/ -hw-path impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/ConditionalBufferTopAttr.v -output-path ./impl/CONF_ee_${test_rsc}rsc-buffers/buffer1/ -top ConditionalBufferTop"
