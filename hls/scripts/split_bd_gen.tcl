# Helper procedures
proc run_python {pypath arglist} {
    # some magic because vivado hates python
    set pp_tmp ::env(PYTHONPATH)
    set ph_tmp ::env(PYTHONHOME)
    unset ::env(PYTHONPATH)
    unset ::env(PYTHONHOME)

    #actually run the python code
    set output [exec python $pypath {*}$arglist ]

    # some magic because vivado hates python
    set ::env(PYTHONPATH) pp_tmp
    set ::env(PYTHONHOME) ph_tmp

    return $output
}

# Hardware generation procedures
proc import_hls { fldr ip_name } {
    #path should be up to partition_*
    global PATH

    set sub_pth "${fldr}/${ip_name}_hls_prj"
    set repo_tmp [get_property ip_repo_paths [current_project] ]
    lappend repo_tmp $PATH/$sub_pth/solution/impl/ip
    #add the layers to IP
    set_property ip_repo_paths $repo_tmp [current_project]
    update_ip_catalog
}

proc generate_split_hardware { BOARD PORT_WIDTH FREQ } { 

    global PATH
    global dir_name
    global NET
    global PART      

    puts "WARNING: ONLY GENERATES FOR PARTITION 0"
    
    # create design
    create_bd_design    "design_1"
    current_bd_design   "design_1"

    # setup
    set parentCell [get_bd_cells /]
    set parentObj [get_bd_cells $parentCell]
    set parentType [get_property TYPE $parentObj]  
    set oldCurInst [current_bd_instance .]
    current_bd_instance $parentObj

    # Create interface ports
    set DDR         [ create_bd_intf_port -mode Master \
        -vlnv xilinx.com:interface:ddrx_rtl:1.0                      DDR       ]
    set FIXED_IO    [ create_bd_intf_port -mode Master \
        -vlnv xilinx.com:display_processing_system7:fixedio_rtl:1.0  FIXED_IO  ]

    ########################  instantiate general board hw  ###########################

    set hp_in_ic    [ create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1  hp_in_ic]
    set hp_out_ic   [ create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1  hp_out_ic]
    set ps      [ create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5    ps      ]
    set rst     [ create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0        rst     ]
    #input output fifos
    set in_fifo     [create_bd_cell -type ip -vlnv xilinx.com:ip:axis_data_fifo:2.0     in_fifo ]
    set out_fifo    [create_bd_cell -type ip -vlnv xilinx.com:ip:axis_data_fifo:2.0     out_fifo]
    # axi DMA block
    set dma     [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1                dma     ]


    ############################## update IP parameters ################################
    
    # set board processor preset (should be zc706 for me)
    if       { $BOARD == "xilinx.com:zc702:part0:1.4" } {
        set_property -dict [list CONFIG.preset {ZC702}] $ps
    } elseif { $BOARD == "xilinx.com:zc706:part0:1.4" } {
        set_property -dict [list CONFIG.preset {ZC706}] $ps
    } elseif { $BOARD == "em.avnet.com:zed:part0:1.4" } {
        set_property -dict [list CONFIG.preset {ZedBoard}] $ps
    }

    # setting processor properties
    set_property -dict [list \
        CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ $FREQ \
        CONFIG.PCW_USE_FABRIC_INTERRUPT {1} \
        CONFIG.PCW_IRQ_F2P_INTR {1} \
    ] $ps

    # TODO: update for number of ports used
    set_property -dict [list \
        CONFIG.PCW_USE_S_AXI_HP0 {1} \
        CONFIG.PCW_S_AXI_HP0_DATA_WIDTH $PORT_WIDTH
    ] $ps

    set_property -dict [list \
        CONFIG.PCW_USE_S_AXI_HP1 {1} \
        CONFIG.PCW_S_AXI_HP1_DATA_WIDTH $PORT_WIDTH
    ] $ps

    # setting input/output interconnect properties
    set_property -dict [ list \
       CONFIG.NUM_MI {1} \
       CONFIG.NUM_SI {1} \
    ] $hp_in_ic

    set_property -dict [ list \
       CONFIG.NUM_MI {1} \
       CONFIG.NUM_SI {1} \
    ] $hp_out_ic

    # setting dma input/output fifo params
    puts "WARNING: defaulting to 32 bits of data (4 bytes)"
    set_property -dict [list CONFIG.TDATA_NUM_BYTES.VALUE_SRC USER] $in_fifo
    set_property -dict [list CONFIG.TDATA_NUM_BYTES {4} CONFIG.FIFO_DEPTH {256}] $in_fifo
    set_property -dict [list CONFIG.TDATA_NUM_BYTES.VALUE_SRC USER] $out_fifo
    set_property -dict [list CONFIG.TDATA_NUM_BYTES {4} CONFIG.FIFO_DEPTH {256}] $out_fifo

    # setting DMA properties #NOTE axis_s2mm is automagically sized
    set_property -dict [list \
        CONFIG.c_include_sg {0} \
        CONFIG.c_sg_length_width {26} \
        CONFIG.c_sg_include_stscntrl_strm {0} \
        CONFIG.c_m_axis_mm2s_tdata_width {32} \
        CONFIG.c_mm2s_burst_size {256} \
        CONFIG.c_s2mm_burst_size {256} \
        CONFIG.c_addr_width $PORT_WIDTH \
    ] $dma

    puts "Updated properties for top level"

    ####################### create connections for top level ip ########################
    # mm2s interconnect -> hp0
    connect_bd_intf_net -intf_net   hp_in_ic_connect \
                                    [get_bd_intf_pins hp_in_ic/M00_AXI  ] \
                                    [get_bd_intf_pins ps/S_AXI_HP0      ]
    connect_bd_intf_net             [get_bd_intf_pins dma/M_AXI_MM2S    ] \
                                    [get_bd_intf_pins hp_in_ic/S00_AXI  ]
    # s2mm interconnect -> hp1
    connect_bd_intf_net -intf_net   hp_out_ic_connect \
                                    [get_bd_intf_pins hp_out_ic/M00_AXI ] \
                                    [get_bd_intf_pins ps/S_AXI_HP1      ]
    connect_bd_intf_net             [get_bd_intf_pins dma/M_AXI_S2MM    ] \
                                    [get_bd_intf_pins hp_out_ic/S00_AXI ]
    # connect ps ddr to DDR output
    connect_bd_intf_net -intf_net   ps_DDR \
                                    [get_bd_intf_ports DDR              ] \
                                    [get_bd_intf_pins ps/DDR            ]
    # connect ps fixed io to FIXED_IO output
    connect_bd_intf_net -intf_net   ps_FIXED_IO \
                                    [get_bd_intf_ports FIXED_IO         ] \
                                    [get_bd_intf_pins ps/FIXED_IO       ]
    # connect in/out fifo to DMA
    connect_bd_intf_net             [get_bd_intf_pins dma/M_AXIS_MM2S   ] \
                                    [get_bd_intf_pins in_fifo/S_AXIS    ]
    connect_bd_intf_net             [get_bd_intf_pins dma/S_AXIS_S2MM   ] \
                                    [get_bd_intf_pins out_fifo/M_AXIS   ]
    # connect clocks
    connect_bd_net -net pl_clk \
        [get_bd_pins hp_in_ic/ACLK          ] \
        [get_bd_pins hp_out_ic/ACLK         ] \
        [get_bd_pins hp_in_ic/M00_ACLK      ] \
        [get_bd_pins hp_out_ic/M00_ACLK     ] \
        [get_bd_pins hp_in_ic/S00_ACLK      ] \
        [get_bd_pins hp_out_ic/S00_ACLK     ] \
        [get_bd_pins ps/FCLK_CLK0           ] \
        [get_bd_pins ps/M_AXI_GP0_ACLK      ] \
        [get_bd_pins ps/S_AXI_HP0_ACLK      ] \
        [get_bd_pins ps/S_AXI_HP1_ACLK      ] \
        [get_bd_pins in_fifo/s_axis_aclk    ] \
        [get_bd_pins out_fifo/s_axis_aclk   ] \
        [get_bd_pins dma/s_axi_lite_aclk    ] \
        [get_bd_pins dma/m_axi_mm2s_aclk    ] \
        [get_bd_pins dma/m_axi_s2mm_aclk    ] \
        [get_bd_pins rst/slowest_sync_clk   ]

    # connecting processor to external reset
    connect_bd_net -net ps_reset \
        [get_bd_pins ps/FCLK_RESET0_N       ] \
        [get_bd_pins rst/ext_reset_in       ]

    #[get_bd_pins ctrl/ARESETN   ]
    connect_bd_net -net interconnect_reset \
        [get_bd_pins hp_in_ic/ARESETN           ] \
        [get_bd_pins hp_out_ic/ARESETN          ] \
        [get_bd_pins rst/interconnect_aresetn   ]

    # connecting reset block to reset of all peripherals
    connect_bd_net -net peripheral_reset \
        [get_bd_pins hp_in_ic/M00_ARESETN   ] \
        [get_bd_pins hp_out_ic/M00_ARESETN  ] \
        [get_bd_pins hp_in_ic/S00_ARESETN   ] \
        [get_bd_pins hp_out_ic/S00_ARESETN  ] \
        [get_bd_pins in_fifo/s_axis_aresetn ] \
        [get_bd_pins out_fifo/s_axis_aresetn] \
        [get_bd_pins dma/axi_resetn         ] \
        [get_bd_pins rst/peripheral_aresetn ]

    ########################  instantiate network hw       ###########################

    #make list of ips - names should be fine
    set layer_list [run_python $::env(FPGACONVNET_HLS)/tools/split_hw_helper.py \
        [list -p ../$NET.json -pi 0 get_layers] ]

    
    set ip_num [llength $layer_list]
    incr ip_num
    puts "Number of IPs: $ip_num"
    
    # create main concat instance
    set irq_c [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 irq_c]
    set_property -dict [list CONFIG.NUM_PORTS {3} ] $irq_c
    connect_bd_net [get_bd_pins dma/mm2s_introut] [get_bd_pins irq_c/In0]
    connect_bd_net [get_bd_pins dma/s2mm_introut] [get_bd_pins irq_c/In1]
    connect_bd_net [get_bd_pins irq_c/dout] [get_bd_pins ps/IRQ_F2P]
    
    set ip_cell_list { }
    # create network layer only concat instance for interrupts (minus top level)
    #set intr_cc [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 intr_cc]
    #lappend ip_cell_list $intr_cc
    #set_property -dict [list CONFIG.NUM_PORTS [ expr $ip_num - 1 ] ] $intr_cc
    # create reduction AND gate
    #set intr_red [create_bd_cell -type ip -vlnv xilinx.com:ip:util_reduced_logic:2.0 intr_red]
    #lappend ip_cell_list $intr_red
    #set_property -dict [list CONFIG.C_SIZE [ expr $ip_num - 1 ] ] $intr_red
    #connect_bd_net [get_bd_pins intr_cc/dout] [get_bd_pins intr_red/Op1]
    # TODO sdk breaks when reduce output concatenated with other interrupts...
    # leaving unconnected
    #connect_bd_net [get_bd_pins intr_red/Res] [get_bd_pins irq_c/In3]

    # create axi_lite control instance
    set ctrl_ic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 ctrl_ic]
    lappend ip_cell_list $ctrl_ic
    set_property -dict [ list \
       CONFIG.NUM_SI {1} \
       CONFIG.NUM_MI [expr $ip_num + 1] \
    ] $ctrl_ic
    # connect ic slave port to ps
    connect_bd_intf_net [get_bd_intf_pins ps/M_AXI_GP0] [get_bd_intf_pins ctrl_ic/S00_AXI]
    # connect dma slave port
    connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M00_AXI] [get_bd_intf_pins dma/S_AXI_LITE]
    # connect clocks, reset (to periph and ic)
    connect_bd_net -net pl_clk              [get_bd_pins ctrl_ic/ACLK       ]
    connect_bd_net -net pl_clk              [get_bd_pins ctrl_ic/S00_ACLK   ]
    connect_bd_net -net interconnect_reset  [get_bd_pins ctrl_ic/ARESETN    ]
    connect_bd_net -net peripheral_reset    [get_bd_pins ctrl_ic/S00_ARESETN]
        
    for {set s_idx 0} {$s_idx < [expr $ip_num + 1]} {incr s_idx} {
        # connect clocks, reset (to periph and ic)
        set ctrl_m [format "%02d" $s_idx]
        connect_bd_net -net pl_clk              [get_bd_pins ctrl_ic/M${ctrl_m}_ACLK    ]
        connect_bd_net -net peripheral_reset    [get_bd_pins ctrl_ic/M${ctrl_m}_ARESETN ]
    }
    
    # add top layer to IP
    import_hls ${NET}_top $NET
    set net_cell [create_bd_cell -type ip -vlnv xilinx.com:hls:${NET}_top:1.0 ${NET} ]
    lappend ip_cell_list $net_cell
    # top layer connections 
    connect_bd_net -net pl_clk              [get_bd_pins ${NET}/ap_clk]
    connect_bd_net -net peripheral_reset    [get_bd_pins ${NET}/ap_rst_n]
    connect_bd_net      [get_bd_pins ${NET}/interrupt       ] \
                        [get_bd_pins irq_c/In2              ]
    # connect top axilite port
    connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M01_AXI   ] \
                        [get_bd_intf_pins ${NET}/s_axi_ctrl ]
    # connect dma block axis in/out
    connect_bd_intf_net [get_bd_intf_pins ${NET}/dma_in     ] \
                        [get_bd_intf_pins in_fifo/M_AXIS    ]
    connect_bd_intf_net [get_bd_intf_pins ${NET}/dma_out    ] \
                        [get_bd_intf_pins out_fifo/S_AXIS   ]
    
    puts "Starting layer loop" 
    set ivar 0
    foreach lyr $layer_list {
        # add the layers to IP
        import_hls $lyr $lyr
        # create layer instances
        lappend ip_cell_list [create_bd_cell -type ip -vlnv xilinx.com:hls:${lyr}_top:1.0 ${lyr} ]
        connect_bd_net -net pl_clk [get_bd_pins ${lyr}/ap_clk] ; # connect clock
        connect_bd_net -net peripheral_reset [get_bd_pins ${lyr}/ap_rst_n] ; # connect reset
        # connect component interrupts
        #connect_bd_net [get_bd_pins ${lyr}/interrupt] [get_bd_pins intr_cc/In${ivar}]
        # connect axi lite ports to ic
        set ctrl_m [format "%02d" [expr $ivar + 2]] ; # generate leading zero
        connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M${ctrl_m}_AXI] \
                            [get_bd_intf_pins ${lyr}/s_axi_ctrl]
        incr ivar
    }
    #debug save
    save_bd_design
    puts "IP CELL LIST HERE: $ip_cell_list"

    # connect top to in/out
        # another python function me thinks... to find input and output layers
    set p_in [run_python $::env(FPGACONVNET_HLS)/tools/split_hw_helper.py \
        [list -p ../$NET.json -pi 0 get_input] ]
    set p_out [run_python $::env(FPGACONVNET_HLS)/tools/split_hw_helper.py \
        [list -p ../$NET.json -pi 0 get_output] ]
    #puts "partition input: $p_in , partition output: $p_out"
    set in_conn [ connect_bd_intf_net \
        [get_bd_intf_pins ${NET}/in_0_V_data_V   ] \
        [get_bd_intf_pins ${p_in}/in_0_V_data_V  ] ]
    set out_conn [ connect_bd_intf_net \
        [get_bd_intf_pins ${NET}/out_0_V_data_V  ] \
        [get_bd_intf_pins ${p_out}/out_0_V_data_V] ]
    ##### BATCH INFORMATION #####
    set in_conn [ connect_bd_intf_net \
        [get_bd_intf_pins ${NET}/in_0_V_batchid_V   ] \
        [get_bd_intf_pins ${p_in}/in_0_V_batchid_V  ] ]
    set out_conn [ connect_bd_intf_net \
        [get_bd_intf_pins ${NET}/out_0_V_batchid_V  ] \
        [get_bd_intf_pins ${p_out}/out_0_V_batchid_V] ]

    puts "connecting layers..."
    #debug save
    current_bd_instance $oldCurInst
    save_bd_design

    ### NEEDED TO STORE EXIT LAYER INPUT LAYERS ###
    set exit_layer_preds { }
    set ctrl_layers { }

    # connect layers to each other TODO make this a proc (function)
    foreach lyr $layer_list {
        # python: get connected layer, get coarse(out)
        set results [run_python $::env(FPGACONVNET_HLS)/tools/split_hw_helper.py \
            [list -p ../$NET.json -pi 0 get_conn -n $lyr] ]
        set coarse [lindex $results end]
        set lyrs_out [lreplace $results end end]
        set out_len [llength $lyrs_out]

        if {[expr $out_len == 0]} {
            puts "FOUND layer without output DATA connections: $lyr"
            lappend ctrl_layers $lyr
            continue
        }

        #foreach lyr_o $lyrs_out
        for {set op_idx 0} {$op_idx < $out_len} {incr op_idx} {
            set lyr_o [lindex $lyrs_out $op_idx]
            puts "crs: $coarse lyr out: $lyr_o"

            # check if there are multiple layers out
            ### NOTE this means it is a split layer ###
            if {[expr $out_len > 1]} {
                #error "LIST NOT SUPPORTED (yet)"
                #puts "Results: $results, Layers out: $lyrs_out (multiple layers out)"
                # form of : out_opidx_crsidx_V_batchid_V
                #           out_opidx_crsidx_V_data_V
                if {[expr $coarse == 1]} {
                    # stupid reordering of output name string
                    #connect out to in
                    connect_bd_intf_net \
                        [get_bd_intf_pins ${lyr}/out_V_data_V_${op_idx}_0 ] \
                        [get_bd_intf_pins ${lyr_o}/in_0_V_data_V]
                    ##### BATCH INFORMATION #####
                    connect_bd_intf_net \
                        [get_bd_intf_pins ${lyr}/out_V_batchid_V_${op_idx}_0 ] \
                        [get_bd_intf_pins ${lyr_o}/in_0_V_batchid_V]
                    #debug save
                    current_bd_instance $oldCurInst
                    save_bd_design
                } else {
                    for {set crs_idx 0} {$crs_idx < $coarse} {incr crs_idx} {
                        #connect out to in
                        connect_bd_intf_net \
                            [get_bd_intf_pins ${lyr}/out_${op_idx}_${crs_idx}_V_data_V ] \
                            [get_bd_intf_pins ${lyr_o}/in_${crs_idx}_V_data_V]
                        ##### BATCH INFORMATION #####
                        connect_bd_intf_net \
                            [get_bd_intf_pins ${lyr}/out_${op_idx}_${crs_idx}_V_batchid_V ] \
                            [get_bd_intf_pins ${lyr_o}/in_${crs_idx}_V_batchid_V]
                        #debug save
                        current_bd_instance $oldCurInst
                        save_bd_design
                    }
                }
            } else {
                # Only one output layer
                # IF layer is the same as current layer - IGNORE (final output)
                if {![string equal $lyr $lyr_o]} {
                    #puts "Results: $results, Layers out: $lyrs_out "
                    #puts "Layer-$lyr"

                    if {[string equal $lyr_o $p_out]} {
                        # output layer is the exit layer - mode complicated to connect
                        puts "Ignoring exit connections as output (for now)"
                        lappend exit_layer_preds $lyr
                        #puts "Exit layer predecessors:$exit_layer_preds"
                    } else {
                        #puts "Connecting $lyr to $lyr_o @ $coarse"
                        # iterate over coarse and connect
                        for {set crs_idx 0} {$crs_idx < $coarse} {incr crs_idx} {
                            #connect out to in
                            connect_bd_intf_net \
                                [get_bd_intf_pins ${lyr}/out_${crs_idx}_V_data_V ] \
                                [get_bd_intf_pins ${lyr_o}/in_${crs_idx}_V_data_V]
                            ##### BATCH INFORMATION #####
                            connect_bd_intf_net \
                                [get_bd_intf_pins ${lyr}/out_${crs_idx}_V_batchid_V ] \
                                [get_bd_intf_pins ${lyr_o}/in_${crs_idx}_V_batchid_V]
                            #debug save
                            current_bd_instance $oldCurInst
                            save_bd_design
                        }
                    }
                } 
            }
        }
    }

    ########## CONNECT Control layers ###########
    # run python get_conn with control flag
    # number of control layers
    puts "List of control layers: $ctrl_layers"
    foreach ctrl_lyr $ctrl_layers {
        puts "Control layer: $ctrl_lyr"
        set results [run_python $::env(FPGACONVNET_HLS)/tools/split_hw_helper.py \
            [list -p ../$NET.json -pi 0 get_conn -n $ctrl_lyr -c] ]
        set ctrl_out_size [lindex $results end]
        set lyrs_out [lreplace $results end end]

        # TODO allow the exit merge to have coarse folding, per layer???
        for {set ctrl_idx 0} {$ctrl_idx < $ctrl_out_size} {incr ctrl_idx} {
            set lyr_o [lindex $lyrs_out $ctrl_idx]
            # connecting input layer to exit
            #connect out to in
            connect_bd_intf_net \
                [get_bd_intf_pins ${ctrl_lyr}/out_${ctrl_idx}_V_data ] \
                [get_bd_intf_pins ${lyr_o}/ctrl_in_V_data]
            # TODO allow the exit merge to have coarse folding, per layer???
            ##### BATCH INFORMATION #####
            connect_bd_intf_net \
                [get_bd_intf_pins ${ctrl_lyr}/out_${ctrl_idx}_V_batchid_V ] \
                [get_bd_intf_pins ${lyr_o}/ctrl_in_V_batchid_V]
            #debug save
            current_bd_instance $oldCurInst
            save_bd_design
        }
    }
    
    ########## CONNECT exit predecessors ###########
    # length is number of inputs tp exit merge
    set in_len [llength $exit_layer_preds]
    # TODO allow the exit merge to have coarse folding, per layer???
    set exit_coarse 1
    for {set ip_idx 0} {$ip_idx < $in_len} {incr ip_idx} {
        set lyr_i [lindex $exit_layer_preds $ip_idx]
        # connecting input layer to exit
        #connect out to in
        connect_bd_intf_net \
            [get_bd_intf_pins ${p_out}/exits_${ip_idx}_V_data_V ] \
            [get_bd_intf_pins ${lyr_i}/out_0_V_data_V]
        # TODO allow the exit merge to have coarse folding, per layer???
        ##### BATCH INFORMATION #####
        connect_bd_intf_net \
            [get_bd_intf_pins ${p_out}/exits_${ip_idx}_V_batchid_V ] \
            [get_bd_intf_pins ${lyr_i}/out_0_V_batchid_V]
        #debug save
        current_bd_instance $oldCurInst
        save_bd_design
    }

    #create hierarchy
    group_bd_cells ${NET}_network {*}$ip_cell_list

    ############### performing final checks, addressing, saving ###############
    puts "Performing final checks!"
    # update base addresses (auto assign)
    assign_bd_address
    #puts "Assigned addresses"
    
    # save design
    current_bd_instance $oldCurInst
    #puts "something with current old inst done"
    save_bd_design
    #puts "saved bd"
    
    # regenerate layout
    regenerate_bd_layout
    #puts "re genned layout"

    # debug tool when ip imports break
    #report_ip_status

    # promote failed connection to error
    set_msg_config -id {BD 41-759} -new_severity {ERROR}
    # validate design
    validate_bd_design
    #puts "validated design"
    current_bd_instance $oldCurInst
    save_bd_design
    puts "FINISHED BD GENERATION!"
}

proc version_checker {verlim} {
    # xilinx hates backwards compatibility 
    # who knows if this will help
    #
    # if the version specified is later than current, return true

    # get version & remove leading v
    set curr_ver [string trim [lindex [version] 1] "v"]
    set res [expr $curr_ver > $verlim]
    return $res
}

proc impl_split_hardware {pth proj} {
    # generate outputs, run synth, impl, bitstream gen
    # overlapping names means OOC per IP required
    # need to do individual synth of each IP and cache
    # NOTE if you just go straight from bd gen then it's fine

    #MAKE HDL WRAPPER AND SET AS TOP FILE
    make_wrapper -files \
        [get_files $pth/$proj/project_1/project_1.srcs/sources_1/bd/design_1/design_1.bd] -top
    add_files -norecurse \
        $pth/$proj/project_1/project_1.srcs/sources_1/bd/design_1/hdl/design_1_wrapper.v
    
    #RUN SYNTH AND IMPL - without all the reseting stuff, defaults to .xci repr for imported IP
    launch_runs impl_1 -to_step write_bitstream -jobs 16
    if {[version_checker 2021.2]} {
        wait_on_runs impl_1
    } else {
        wait_on_run impl_1
    }
    
    # EXPORTING HW + bitstream
    file mkdir $pth/$proj/project_1/project_1.sdk
    file copy -force \
        $pth/$proj/project_1/project_1.runs/impl_1/design_1_wrapper.sysdef \
        $pth/$proj/project_1/project_1.sdk/design_1_wrapper.hdf
}
