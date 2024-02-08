# get parameters
set name [lindex $argv 2]
set type [lindex $argv 3]
set clk  [lindex $argv 4]
set fpga [lindex $argv 5]

cd modules/${name}

open_project ${name}_prj
set_top ${name}_top

add_files src/${name}.cpp       -cflags "-I../../../include -I./src/ -I./tb/ -I./data/"
add_files -tb tb/${name}_tb.cpp -cflags "-I../../../include -I./src/ -I./tb/ -I./data/ -lyaml-cpp"

open_solution "solution"

set_part $fpga -tool vivado
config_dataflow -default_channel fifo -fifo_depth 2 
create_clock -period $clk -name default

# define vivado hls procedures
proc csim   {} { csim_design -compiler gcc -mflags "-j 8" }
proc csynth {} { csynth_design } 
proc cosim  {} { cosim_design -rtl verilog -tool xsim -disable_deadlock_detection }
proc export {} { export_design -flow impl -rtl verilog -format ip_catalog }
# run hls tool
if { $type == "sim" } {
    csim
} elseif { $type == "synth" } {
    csynth
} elseif { $type == "cosim" } {
    cosim 
} elseif { $type == "impl" } {
    export
}
cd ../..
exit
