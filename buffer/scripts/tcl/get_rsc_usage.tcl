################################################################################
# vivado -mode batch -notrace -source gen_hw.tcl -tclargs argv[0]
#  ( argv 1 : network name          )
#  ( argv 2 : fpga part name        )
#  ( argv 3 : fpga board part       )
#  ( argv 4 : board frequency       )
#  ( argv 5 : port width            )
#  ( argv 6 : weights reloading on  )
################################################################################

# get script location
set script_loc [file dirname [file normalize [info script]]]

# load getopt script
source $script_loc/tcl_getopt.tcl

# get input arguments
set args [ lindex $argv 0 ]

# get arguments

## part specification
getopt $args -part part "xc7z020clg484-1"
# getopt $args -part part "xc7z045ffg900-2"
# getopt $args -part part "xczu7ev-ffvc1156-2-e"
getopt $args -board board ""
#"xilinx.com:zc702:part0:1.4"
# getopt $args -freq freq 200
getopt $args -freq freq 350

## paths
getopt $args -prj-path prj_path
getopt $args -hw-path hw_path
getopt $args -output-path out_path ""
getopt $args -top top

# parts
# - zcu106: xczu7ev-ffvc1156-2-e
# - zc706: xc7z045ffg900-2
# - zc702: xc7z020clg484-1

# strip quotes from part
set part [ string map {"\"" ""} $part ]

# Create Vivado Project
create_project -force rsc_prj $prj_path -part $part

# Set FPGA device/board
if { $board != "" } {
    set_property board_part $board [current_project]
}

# add verilog file to project
add_files -norecurse $hw_path
# add_files -fileset constrs_1 $script_loc/tmp.xdc

# set top module
set_property top $top [current_fileset]

# update hierachy
update_compile_order -fileset sources_1

# run out of context synthesis
synth_design -mode out_of_context -top $top -part $part -directive AreaOptimized_high -retiming
write_checkpoint -force $prj_path/post_synth

# set the clock frequency
set period [expr {1000.0/$freq}]
create_clock -name clock -period $period [get_ports clock]

#report_utilization
if { $out_path != "" } {
    set reportLines [split [report_utilization -hierarchical -return_string] "\n"]
    set csv_file "${out_path}/resource_report.csv"
    set fh [open $csv_file w]
    set writelines false
    foreach line $reportLines {
        if {[regexp {\+[+-]+} $line]} {
        set writelines true
        }
        if {$writelines && [regexp {^\|} $line]} {
            puts $fh [regsub -all {\|} [regsub -all {.\|.} $line ","] ""]
        }
    }
    close $fh
} else {
    report_utilization
}

#report_timing_summary
if { $out_path != "" } {
    set reportLines [split [report_timing_summary -return_string] "\n"]
    set csv_file "${out_path}/timing_report.csv"
    set fh [open $csv_file w]
    set csv_file_full "${out_path}/timing_report_full.csv"
    set fh_full [open $csv_file_full w]
    foreach line $reportLines {
        puts $fh_full $line
        if {[regexp {^(Min Period|Setup|Hold|PW)} $line]} {
            puts $fh $line
        }
    }
    close $fh
} else {
    report_timing_summary
}

