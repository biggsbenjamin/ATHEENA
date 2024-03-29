# ATHEENA (and fpgaConvNet) HLS

This is CNN-to-FPGA mapping framework designed to find the optimal implementation of a CNN architecture on an FPGA for power, latency and throughput driven designs.

## Setup

_This project has only been verified on Ubuntu 20.04_

The following programmes are needed:

1. Vivado 2019.1 (with y2k patch)
2. yaml-cpp (version 0.5.3)

This uses the same python environment as the optimiser.

### Vivado setup

To install Vivado 2019.1:

1. First [download](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools/2019-1.html) from the Xilinx website.

2. Install the y2k22 patch according to these [instructions](https://support.xilinx.com/s/article/76960?language=en_US).

3. Add the following to your ~/.bashrc file:

```
source /tools/Xilinx/Vivado/2019.1/settings64.sh
source /tools/Xilinx/SDK/2019.1/settings64.sh
export FPGACONVNET_ROOT=(path to repo)/ATHEENA_fccm_artifacts/hls
export FPGACONVNET_HLS=(path to repo)/ATHEENA_fccm_artifacts/hls
export FPGACONVNET_OPTIMISER=(path to repo)/ATHEENA_fccm_artifacts/optimiser
```

4. Once installed, you will also need to add a license server to your .bashrc file.

5. You will need to setup JTAG drivers to program a device. To do so, execute the following script:

```
/tools/Xilinx/Vivado/2019.1/data/xicom/cable_drivers/lin64/install_script/install_drivers/install_drivers
```

For more information, visit [here](https://www.xilinx.com/support/answers/59128.html).

Finally, there is a known [bug](http://svn.clifford.at/handicraft/2017/vivadobugs/vivadobug04.txt) to do with C++ libraries. A workaround for this is adding the `mpfr.h` and `gmp.h` headers manually. For this project, you need to create a header file `include/system.hpp` which includes the following:

```C
#ifndef SYSTEM_HPP_
#define SYSTEM_HPP_

#include "(path to Vivado 2019.1)/include/gmp.h"
#include "(path to Vivado 2019.1)/include/mpfr.h"

#endif
```

### Examples

*Please run the buffer generation before using the hls tools.*

To regenerate the results for the artifacts in the paper:

A1 : `./hls/test/partitions/design_A1/`
A2 : `./hls/test/partitions/design_A2/`
A3 : `./hls/test/partitions/design_A3/`

These folders contain:

- `.json` file with the hardware description (generated by the optimiser).
- `.c` host code that runs the project on the ZC706 board.
- `split_run.sh` script that regenerates the HLS files and Vivado project.
- Run the generation from inside the folder, using `./split_run.sh -a -v`.
> **Note**: path information is embedded as defaults in the `split_run.sh`

This will run the HLS compilation for the layers specified in the .json file in this folder (this will take a while).

### Running your own version
To run your own version:

1. Copy the json file generated by the optimiser after the merge stage into a new folder in `./test/partitions/(example)`.

2. Navigate to `./test/partitions/` and run `./../../scripts/split_run.sh -a -v -n (network and folder name) -p (.json file name) -m (path to onnx model)`.

This should run through the HLS component generation, stitch the components in a Vivado project, run sythesis and place and route, and generate the host code needed to run bitstream.

### Using the SDK

The final step requires some manual integration with the Vivado SDK and assumes that the target board is the ZC706 (used in the paper).

1. Open the resulting `project_1` in `test/partitions/(network name)/partition_0/(network name)_hw_prj`

2. Export the hardware + bitstream: `File > Export > Export Hardware`. Check `include bitstream`.

3. Launch the SDK: `File > Launch SDK`

![New Application Project](./sdk_imgs/application_proj.png?raw=true)

4. Generate the FSBL: `File > New > Application Project`. Provide a project name and select the exported hw platform 0. Hit `Next` and select `Zynq FSBL` and hit `Finish`.

![FSBL template project](./sdk_imgs/fsbl.png?raw=true)

5. Generate the host code: `File > New > Application Project`. Provide a project name and select the exported hw platform 0. Hit `Next` and select `Hello world` and hit `Finish`.

![hello world template project](./sdk_imgs/hellow.png?raw=true)

6. In this project, open `hello_world.c` and replace the contents with  `branchy_lenet_eg_host_code.c`

![hello world replace code](./sdk_imgs/hellow_host.png?raw=true)

7. Add the xilffs support to the host code (hello world) BSP using `system.mss > modify bsp`

![edit system mss file](./sdk_imgs/find_mss.png?raw=true)

![add ffs support](./sdk_imgs/xilffs.png?raw=true)

8. Insert SD card loaded with `i0.bin` file copied from `./hls/test/data/test/partitions/(network name)/partition_0/data/input0.bin`

9. Run the FSBL project on the board and then .

![run fsbl](./sdk_imgs/run_fsbl.png?raw=true)

10. Program with the bitstream.

![program device](./sdk_imgs/program_device.png?raw=true)

11. Run the host code (hello world) project. Debug mode may be required as there are some issues printing over UART.

![run host code](./sdk_imgs/run_hellow.png?raw=true)

12. Add a breakpoint as the code may not terminate gracefully.

![add break point if needed](./sdk_imgs/brkpnt_if_needed.png?raw=true)

The results of the test, reported in ms is shown in this variable:

![results reported](./sdk_imgs/thruput_record.png?raw=true)

### Comparing the Hardware Classification Results with Software (PyTorch)

1. Remove the SD card from the board. The following file should now be present `O0.BIN`, generated by the processor to store the results from the accelerator.

2. Run the following command to compare these binary file with the equivalent generated by the PyTorch *as part of* `split_run.sh`:

```Shell
python $FPGACONVNET_HLS/scripts/check_bin.py \
-gp test/partitions/(network name)/partition_0/data/OUTPUT0_INNERPRODUCT2_0.bin test/partitions/(network name)/partition_0/data/OUTPUT1_INNERPRODUCT35_0.bin -ap (path to SD card)/O0.BIN -e 0.5 -ee
```
> **Note**: `-e 0.5` defines the tolerance of the checker due to hardware quantisation. `-ee` denotes an early-exit network (the script has an equivalent checker for non-early-exit networks).

If there is a significant deviation in *any part* of the class values produced. The program will report an error. If no errors are reported then the largest difference (and the % of the tolerance) will be reported.
