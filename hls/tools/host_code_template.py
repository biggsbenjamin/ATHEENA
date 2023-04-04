import sys
import numpy as np
import os
import fpgaconvnet_optimiser.proto.fpgaconvnet_pb2
from onnx_data import gen_layer_name, get_layer_from_partition

sys.path.append(os.environ.get("FPGACONVNET_OPTIMISER"))
sys.path.append(os.environ.get("FPGACONVNET_HLS"))

########################################################
################## Host Code Template ##################
########################################################

hc_template = """/* THIS CODE IS AUTO GENERATED
* This application configures UART 16550 to baud rate 9600.
* PS7 UART (Zynq) is not initialized by this application, since
* bootrom/bsp configures it to baud rate 115200
*
* ------------------------------------------------
* | UART TYPE   BAUD RATE                        |
* ------------------------------------------------
*   uartns550   9600
*   uartlite    Configurable only in HW design
*   ps7_uart    115200 (configured by bootrom/bsp)
*/

#include <stdio.h>
#include <stdlib.h>
#include "platform.h"
#include "xil_printf.h"
#include "xparameters.h"
#include "xil_cache.h"
//sd header
#include "ff.h"
//dma header
#include "xaxidma.h"
//timer header
#include "xtime_l.h"

{includes}
//ip config pointers and handlers
XAxiDma axiDMA;
XAxiDma_Config *axiDMA_cfg;

{config_pntrs}
// sd file system from example
FATFS fatfs;
static char input_file[20] = "i0.bin"; //NOTE 20 seems to be max allowed
static char output_file[20] = "o0.bin";
static char *sd_in;
static char *sd_out;

//fcn input and outpt data sample sizes
#define INPUT_SIZE {input_size}
#define OUTPUT_SIZE {output_size}
#define BATCH_SIZE {batch_size}

#define SIZE_IN INPUT_SIZE*BATCH_SIZE
#define SIZE_OUT OUTPUT_SIZE*BATCH_SIZE

{data_type} in_stream[SIZE_IN]; //use ap_fixed type

//DMA addresses (from yt example)
#define MEM_BASE_ADDR 0x01000000
#define RX_BUFF_BASE (MEM_BASE_ADDR + 0x00100000)

// *************** initialisation ****************

void initPeriph() {{
    //initialising dma
    xil_printf("Initialising dma\\n\\r");
    axiDMA_cfg = XAxiDma_LookupConfig(XPAR_AXIDMA_0_DEVICE_ID);
    if (axiDMA_cfg) {{
            int status = XAxiDma_CfgInitialize(&axiDMA,axiDMA_cfg);
            if (status != XST_SUCCESS) {{
                    xil_printf("Error initalising dma\\n");
            }}
    }}
    //disable interrupts (from example)
    XAxiDma_IntrDisable(&axiDMA, XAXIDMA_IRQ_ALL_MASK, XAXIDMA_DEVICE_TO_DMA);
    XAxiDma_IntrDisable(&axiDMA, XAXIDMA_IRQ_ALL_MASK, XAXIDMA_DMA_TO_DEVICE);

    //initialising sd
    FRESULT rc;

    rc = f_mount(&fatfs,"",1);
    if (rc) {{
            xil_printf(" ERROR : f_mount returned %d\\r\\n", rc);
            return XST_FAILURE;
    }}

    {layer_inits}
    return XST_SUCCESS;
}}

// *************** sd card functions ****************

int sd_read( void* dest_addr) {{
    FIL fil;
    FRESULT rc;
    uint length = 0;
    uint bytes_read = 0;
    sd_in = (char *)input_file;
    u32 byte_len = SIZE_IN * sizeof({data_type});
    //open file to read
    rc = f_open(&fil, sd_in, FA_READ);
    if (rc) {{
            xil_printf(" ERROR : %s f_open returned %d\\r\\n", sd_in, rc);
            return XST_FAILURE;
    }}
    // get length of file
    length=f_size(&fil);
    //pointer to beginning of file
    rc = f_lseek(&fil, 0);
    if (rc) {{
            xil_printf(" ERROR : %s f_lseek returned %d\\r\\n", sd_in, rc);
            return XST_FAILURE;
    }}
    //file obj, address to read into, file size, number of bytes actually read
    rc = f_read(&fil, dest_addr, length, &bytes_read);
    if (rc) {{
            xil_printf(" ERROR : %s f_read returned %d\\r\\n", sd_in, rc);
            return XST_FAILURE;
    }}

    //check if bytes read equals to expected number of bytes
    if((bytes_read != byte_len)&&(byte_len != 0)) {{
            xil_printf(" ERROR: File: '%s', Expected size: %d; Actual size: %d\\r\\n", sd_in, byte_len, bytes_read);
            return XST_FAILURE;
    }}
    //close the file
    rc = f_close(&fil);
    if (rc) {{
            xil_printf(" ERROR : %s f_close returned %d\\r\\n", sd_in, rc);
            return XST_FAILURE;
    }}
    //if (FPGACONVNET_DEBUG) {{
    //	xil_printf("(DEBUG) SD card: File '%s' read. Length: %d; Addr.: 0x%08x\\r\\n", sd_in, length, dest_addr);
    //}}
    return XST_SUCCESS;
}}

int sd_write(u32* start_addr) {{
    FIL fil;
    FRESULT rc;
    uint length;
    sd_out = (char *)output_file;
    u32 byte_len = SIZE_OUT * sizeof({data_type});
    rc = f_open(&fil, sd_out, FA_CREATE_ALWAYS | FA_WRITE);
    if (rc) {{
        xil_printf(" ERROR : %s f_open returned %d\\r\\n", sd_out, rc);
        return XST_FAILURE;
    }}
    //length=file_size(&fil);
    rc = f_lseek(&fil, 0);
    if (rc) {{
        xil_printf(" ERROR : %s f_lseek returned %d\\r\\n", sd_out, rc);
        return XST_FAILURE;
    }}
    rc = f_write(&fil, start_addr, byte_len, &length);
    if (rc) {{
        xil_printf(" ERROR : %s f_write returned %d\\r\\n", sd_out, rc);
        return XST_FAILURE;
    }}
    if(length != byte_len) {{
        xil_printf("Expected written bytes: %d. Written bytes: %d\\r\\n", byte_len, length);
        return XST_FAILURE;
    }}
    rc = f_close(&fil);
    if (rc) {{
        xil_printf(" ERROR : %s f_close returned %d\\r\\n", sd_out, rc);
        return XST_FAILURE;
    }}
    //if (FPGACONVNET_DEBUG) {{
    //    xil_printf("(DEBUG) SD card: File '%s' written. Length: %d\\r\\n", sd_out, length);
    //}}
    return XST_SUCCESS;
}}

// *************************** MAIN ******************************

int main() {{
    init_platform();
    print("Hello World\\n\\r");

    // flush and disable caches
    Xil_DCacheFlush();
    Xil_DCacheDisable();

    //initialising layers, dma blocks, sd card
    initPeriph();

    //pointer to dma rx addresses
    u32 *m_dma_buff_rx = (u32*) RX_BUFF_BASE;

    // read from sd and write to input array
    sd_read(in_stream);
    //non sd data
    /*{data_type} data;
	for (int idx=0;idx<SIZE_IN;idx++) {{
		data = idx % 16;
		in_stream[idx] = data;
	}}*/

    // ****************** starting core *****************
    xil_printf("Starting Core\\n\\r");

    //start fcn blocks
{layer_starts}
    //flush buffer caches?
    Xil_DCacheFlushRange((u32)in_stream, SIZE_IN*sizeof({data_type}));
    Xil_DCacheFlushRange((u32)m_dma_buff_rx, SIZE_OUT*sizeof({data_type}));

    //start timer
    //XScuTimer_Start(&timer);
    XTime tStart, tEnd;
    double elapsedTime, diff;

    //setting up simple dma transfers
    //xil_printf("Receive command for DMA\\n\\r");
    XAxiDma_SimpleTransfer(&axiDMA, (u32) m_dma_buff_rx, SIZE_OUT * sizeof({data_type}), XAXIDMA_DEVICE_TO_DMA);
    //xil_printf("Send command for DMA\\n\\r");

    XAxiDma_SimpleTransfer(&axiDMA, (u32) in_stream, SIZE_IN * sizeof({data_type}), XAXIDMA_DMA_TO_DEVICE);

    //start timer
    XTime_GetTime(&tStart);
    //check when dma has finished - total time from ddr -> core -> ddr
    while (XAxiDma_Busy(&axiDMA, XAXIDMA_DEVICE_TO_DMA) || XAxiDma_Busy(&axiDMA, XAXIDMA_DMA_TO_DEVICE));
    //stop timer
    XTime_GetTime(&tEnd);

    diff = 2.0 * (tEnd - tStart);
    //elapsed time calculated in us
    elapsedTime = 1000000*(tEnd-tStart)/(COUNTS_PER_SECOND);

    xil_printf("Output took %llu clock cycles.\\n\\r", diff);
    xil_printf("DMA transactions finished. Timer: %.2f us\\n\\r",elapsedTime);

    //invalidate cache to avoid reading rubbish (shouldnt be needed since disabled)
    //Xil_DCacheInvalidateRange((u32) m_dma_buff_rx, SIZE_OUT * sizeof({data_type}));

    //write finished data to .bin file
    sd_write(m_dma_buff_rx);

    xil_printf("done write\\n\\r");

    cleanup_platform();
    return 0;
}}
"""

# class for host code layer templates
class LayerHostCode:
    def __init__(self, raw_name, lyr_num, net_name):
        self.raw_name=raw_name
        self.lyr_num=lyr_num
        self.NET=net_name.upper()
        self.NAME_TOP="X{}_TOP".format(self.raw_name.upper())
        self.NAME="X{}".format(self.raw_name.upper())
        self.name="{}".format(self.NAME_TOP.lower())
        self.Name="{}{}".format(self.NAME_TOP[0:2],self.name[2:])

        #DEBUG
        #print(self.get_include())
        #print(self.get_code_handlers())
        #print(self.get_layer_inits())
        #print(self.get_layer_starts())

    def get_include(self):
        # return string of include for layer
        inc_str = "#include \"{}.h\"\n".format(self.name)
        return inc_str

    def get_code_handlers(self):
        # gen handler
        hndlr = "{} lyr{};\n".format(self.Name,self.lyr_num)
        # gen cfg pntr
        cfg = "{}_Config *lyr{}_cfg;\n".format(self.Name,self.lyr_num)
        return hndlr+cfg

    def get_layer_inits(self):
        # return code for initialisation of layer
        init ="""
    xil_printf("Initialising fpgaconvnet layer{num}\\n\\r");
    lyr{num}_cfg = {Name}_LookupConfig(XPAR_{NET}_NETWORK_{NAME}_DEVICE_ID);
    if (lyr{num}_cfg) {{
        int status = {Name}_CfgInitialize(&lyr{num}, lyr{num}_cfg);
        if (status != XST_SUCCESS) {{
            xil_printf("Error initalising layer :{num}:\\n\\r");
        }}
    }}
""".format(num=self.lyr_num,Name=self.Name,
        NET=self.NET,NAME=self.NAME[1:])
        return init

    def get_layer_starts(self):
        # return string for layer start command
        strt="    {}_Start(&lyr{});\n".format(self.Name,self.lyr_num)
        return strt
