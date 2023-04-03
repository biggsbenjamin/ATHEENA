################################################################################
# vivado -mode batch -notrace -source gen_hw.tcl -tclargs argv[0]
#  ( argv 1 : network name          )
#  ( argv 2 : fpga part name        )
#  ( argv 3 : fpga board part       )
#  ( argv 4 : board frequency       )
#  ( argv 5 : port width            )
#  ( argv 6 : weights reloading on  )
################################################################################

# get variables
set PART        xc7z020clg484-1
set BOARD       xilinx.com:zc702:part0:1.4
set FREQ        100

set PATH $::env(PWD)
set dir_name "test_prj"

# Create Vivado Project
create_project -force project_1 $PATH/$dir_name -part $PART
# Set FPGA device/board
set_property board_part $BOARD [current_project]

set module [ lindex $argv 0 ]
# set params [ lindex $argv 1 ]

# add verilog file to project
add_files -norecurse impl/${module}.v
add_files -fileset constrs_1 ./tmp.xdc

set_property top $module [current_fileset]

update_compile_order -fileset sources_1
synth_design -mode out_of_context -top $module -part $PART

#report_utilization
set reportLines [split [report_utilization -hierarchical -return_string] "\n"]
set csv_file "resource_report.csv"
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

#report_timing_summary
set reportLines [split [report_timing_summary -return_string] "\n"]
set csv_file "timing_report.csv"
set fh [open $csv_file w]
foreach line $reportLines {
    if {[regexp {^(Setup|Hold|PW)} $line]} {
		puts $fh $line
	}
}
close $fh