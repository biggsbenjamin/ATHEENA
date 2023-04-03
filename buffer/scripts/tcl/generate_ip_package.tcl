# taken from http://lucasbrasilino.com/posts/Vivado-project-for-version-control-how-to-package-an-ip-from-sources/

# create variables for the project
set name [ lindex $argv 0 ]
set v_source [ lindex $argv 1 ]
set top_module [ lindex $argv 2 ]
set output_path [ lindex $argv 3 ]

# create ip properties
set ip_properties [ list \
    vendor "fccm_artifact.co.uk" \
    library "fpgaconvnet" \
    name ${name} \
    version "1.0" \
    taxonomy "/Accelerator" \
    display_name ${name} \
    description "fpgaconvnet layer: ${name}" \
    vendor_display_name "fccm_artifact" \
    company_url "https://fccm_artifact.co.uk" \
]

# copy verilog to the ip directory
file mkdir -force "${output_path}/${name}"
file copy -force ${v_source} "${output_path}/${name}/${name}.v"

# create the project
set ip_project [ create_project -name ${name} -force -dir "./${name}_prj" -ip ]
set_property top ${top_module} [current_fileset]

# read in source files
# read_verilog ${v_source}
read_verilog "${output_path}/${name}/${name}.v"
update_compile_order -fileset sources_1

# package the ip
ipx::package_project -root_dir ${output_path}/${name}
set ip_core [ipx::current_core]
set_property -dict ${ip_properties} ${ip_core}

# save the ip
set_property core_revision 2 ${ip_core}
ipx::update_checksums ${ip_core}
ipx::check_integrity ${ip_core}
ipx::save_core ${ip_core}
# ipx::archive_core ip/${name}.zip [ipx::current_core]

# close the project
close_project
file delete -force "./${name}_prj"
