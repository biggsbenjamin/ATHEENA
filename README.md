[![DOI](https://zenodo.org/badge/606085080.svg)](https://zenodo.org/badge/latestdoi/606085080)

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

./cs setup
```

> **Note**: This will install the most recent version of scala. To check it has worked, run `scala -version` (a restart of the terminal maybe required).

2. Install Scala version 2.12.13 and sbt version 1.4.9

```
cs install scala:2.12.13 && cs install scalac:2.12.13

cs install sbt:1.4.9 && cs install sbtn:1.4.9
```
> **Note**: To check the scala and sbt versions, run `scala -version` and `sbt --script-version`.

3. Regenerate the project for the buffer package.

```
cd ./buffer/

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

To generate an optimised FPGA accelerator description for an Early-Exit network, follow the instructions in `optimiser/README.md`.

To generate the hardware corresponding to the accelerator description, copy the resulting `.json` file into `./hls/test/partitions/(new_folder)` and follow the HLS instructions.

