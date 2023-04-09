[![DOI](https://zenodo.org/badge/606085080.svg)](https://zenodo.org/badge/latestdoi/606085080)

> **Note**: If above DOI is broken, [this one](https://doi.org/10.5281/zenodo.7809222) should be correct.

# ATHEENA FCCM Artifacts

Software and hardware artifacts for FCCM submission 2023

There are three main artifacts:
- Optimiser
- Buffer Hardware Component (and generation)
- HLS-based hardware generation using Vivado

## Full Setup instructions

The optimiser (and HLS generation) has been verified using the following software:

- `conda=4.9.2, 4.10.1`
- `python=3.7`

### Optimiser package and Environment setup

To install this package, run from this directory the following:

```
sudo apt install protobuf-compiler libprotoc-dev
cd ./optimiser/
conda env create -f atheena_opt_hls_p37.yml
conda activate atheena_opt_hls_p37
python atheena_setup.py install 
```

### Scala and Chisel package setup

To install the appropriate software for buffer generation:

> **Note** This module has been verified working for Ubuntu 20.04.6 LTS, Java version 11.0.18, sbt version 1.4.9, [Scala 2.12.13](https://www.scala-lang.org/download/2.12.13.html)

The following instructions are taken from [Chisel's](https://github.com/chipsalliance/chisel3) instructions on environment setup:

1. Install [Coursier](https://docs.scala-lang.org/getting-started/index.html#using-the-scala-installer-recommended-way) and follow the instructions.

```
curl -fL https://github.com/coursier/coursier/releases/latest/download/cs-x86_64-pc-linux.gz | gzip -d > cs && chmod +x cs 
```
```
./cs setup
```

> **Note**: This will install the most recent version of scala. To check it has worked, run `scala -version` (a restart of the terminal maybe required).

2. Install Scala version 2.12.13 and sbt version 1.4.9

```
cs install scala:2.12.13 && cs install scalac:2.12.13
```
```
cs install sbt:1.4.9 && cs install sbtn:1.4.9
```
> **Note**: To check the scala and sbt versions, run `scala -version` and `sbt --script-version`.

3. Regenerate the project for the buffer package.

```
cd ./buffer/
```
```
sbt pack
```

### Vivado setup

To install Vivado 2019.1:

1. First [download](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools/2019-1.html) from the Xilinx website.

2. Install the y2k22 patch according to these [instructions](https://support.xilinx.com/s/article/76960?language=en_US).

3. Add the following to your ~/.bashrc file:

```
export PATH=/tools/Xilinx/Vivado/2019.1/bin:$PATH
export PATH=/tools/Xilinx/SDK/2019.1/bin:$PATH
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

## Generating the Artifacts

To generate an optimised FPGA accelerator description for an Early-Exit network, follow the instructions in `optimiser/README.md`:

### Optimiser instructions (after setup)

1. Run optimiser on the branchy LeNet network description.

```Shell
cd ./optimiser/
```
```Shell
python -m fpgaconvnet_optimiser.tools.dev_script \
    --expr opt_brn \
    --save_name branchy_lenet \
    -o outputs/branchy_lenet \
    --model_path examples/models/atheena/branchy_lenet_20220902.onnx \
    --platform_path examples/platforms/zc706.json \
    --optimiser_path examples/optimiser_example.yml \
    -bs 1024
```

2. Generate the pareto graph for the optimiser results at an early-exit probability of 75% (as in the paper).

```Shell
python -m fpgaconvnet_optimiser.tools.dev_script \
    --expr gen_graph \
    --save_name branchy_lenet_graph \
    -o outputs/branchy_lenet/results/ \
    -i outputs/branchy_lenet/ \
    --profiled_probability 0.75 
```
3. Run the following command to perform a stage merge for all the results in the combined report.

```Shell
python -m fpgaconvnet_optimiser.tools.ee_stage_merger \
    -c outputs/branchy_lenet/results/combined_rpt_eefrac75.txt \
    -j outputs/branchy_lenet/ \
    -on branchy_lenet_merged \
    --output_path outputs/branchy_lenet/merged/
```

4. Copy this `.json` file into a folder in `hls/test/partitions/(example)/`.

For example: 
```Shell
mkdir -p ../hls/test/partitions/branchy_lenet_eg
```
```Shell
cp outputs/branchy_lenet/merged/branchy_lenet_merged_rsc80_thru95000.json ../hls/test/partitions/branchy_lenet_eg/
```

> **Note**: Due to the non-deterministic nature of the optimiser, the above file will have slightly different resource usage and throughput. For the A1-like design use an rsc**30-35** and thru**~19500**. For A2-like, use rsc**45-50** and thru**~45000**. For A3-like design, use rsc**80-90** and thru**95000**.

### Buffer instructions (after setup)

5. Run the following instructions to generate available hardware IP for the buffer layer at different resource allocations.

```Shell
cd ../buffer/
```
```Shell
./gen_buff.sh
```

6. Respond to the prompt with `a`, to generate all the configurations.

### HLS Instructions (after setup)

7. Run the following instructions to start the HLS generation process for the layers based on the hardware description provided. 

```Shell
cd ../hls/test/partitions/
```
```Shell
../../scripts/split_run.sh -a \
    -n branchy_lenet_eg \
    -m $FPGACONVNET_OPTIMISER/examples/models/atheena/branchy_lenet_20220902.onnx \
    -p branchy_lenet_merged_rsc80_thru95000.json \
    -v
```

> **Note**: The `-a` is used to generate all the network layers, the top layer, and the host code. The `-v` flag is used to stitch the resulting network IP layers into a full board design and then run Vivado synthesis and implementation before finally generating the bitstream. The script can be run with or without these flags if only one operation is required.

8. The final step requires some manual integration with the Vivado SDK and assumes that the target board is the ZC706 (used in the paper).
    
    a. Open the resulting `project_1` in `test/partitions/branchy_lenet_eg/partition_0/branchy_lenet_eg_hw_prj`

    b. Export the hardware + bitstream: `File > Export > Export Hardware`. Check `include bitstream`.

    c. Launch the SDK: `File > Launch SDK`

    d. Generate the FSBL: `File > New > Application Project`. Provide a project name and select the exported hw platform 0. Hit `Next` and select `Zynq FSBL` and hit `Finish`.

    e. Generate the host code: `File > New > Application Project`. Provide a project name and select the exported hw platform 0. Hit `Next` and select `Hello world` and hit `Finish`.

    f. In this project, open `hello_world.c` and replace the contents with  `branchy_lenet_eg_host_code.c`

    g. Add the xilffs support to the host code (hello world) BSP using `system.mss > modify bsp`

    h. Insert SD card loaded with `./hls/test/data/pc75/I0.BIN`

    i. Run the FSBL project on the board, upload the bitstream and then run the host code (hello world) project!

### Included Artifacts

As the HLS generation and Vivado Synthesis take a significant amount of time to run, I have included three ATHEENA hardware projects and designs from the paper have been included in this repository.

A1 : `./hls/test/partitions/design_A1/`
A2 : `./hls/test/partitions/design_A2/`
A3 : `./hls/test/partitions/design_A3/`

These folders contain:

- `.json` file with the hardware description (generated by the optimiser).

- `.c` host code that runs the project on the ZC706 board.

- `split_run.sh` script that regenerates the HLS files and Vivado project.

- Run the generation from inside the folder, using `./split_run.sh -a -v`.

A copy of the hardware project with host code for each of these examples can be found and downloaded [here](https://drive.google.com/drive/folders/15Mc-UckojIFMW_R6GzN4vwPkShtwQtSw?usp=sharing)
> **Note**: to unzip use `tar -xzvf a1_hw_artifact.tar.gz` and then opened using Vivado design suite and SDK.
