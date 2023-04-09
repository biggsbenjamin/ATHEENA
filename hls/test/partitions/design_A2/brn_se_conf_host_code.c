/* THIS CODE IS AUTO GENERATED
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

#include "xbrn_se_conf_top.h"
#include "xconvolution13_top.h"
#include "xpooling14_top.h"
#include "xpooling14_squeeze_relu15_top.h"
#include "xrelu15_top.h"
#include "xsplit0_top.h"
#include "xconvolution16_top.h"
#include "xconvolution16_squeeze_pooling17_top.h"
#include "xpooling17_top.h"
#include "xrelu18_top.h"
#include "xrelu18_squeeze_innerproduct2_top.h"
#include "xinnerproduct2_top.h"
#include "xinnerproduct2_squeeze_split1_top.h"
#include "xsplit1_top.h"
#include "xgreater24_top.h"
#include "xbrn_exit_top.h"
#include "xconvolution28_top.h"
#include "xconvolution28_squeeze_pooling29_top.h"
#include "xpooling29_top.h"
#include "xpooling29_squeeze_relu3_top.h"
#include "xrelu3_top.h"
#include "xconvolution31_top.h"
#include "xconvolution31_squeeze_pooling32_top.h"
#include "xpooling32_top.h"
#include "xrelu33_top.h"
#include "xrelu33_squeeze_innerproduct35_top.h"
#include "xinnerproduct35_top.h"

//ip config pointers and handlers
XAxiDma axiDMA;
XAxiDma_Config *axiDMA_cfg;

XBrn_se_conf_top lyr0;
XBrn_se_conf_top_Config *lyr0_cfg;
XConvolution13_top lyr1;
XConvolution13_top_Config *lyr1_cfg;
XPooling14_top lyr2;
XPooling14_top_Config *lyr2_cfg;
XPooling14_squeeze_relu15_top lyr3;
XPooling14_squeeze_relu15_top_Config *lyr3_cfg;
XRelu15_top lyr4;
XRelu15_top_Config *lyr4_cfg;
XSplit0_top lyr5;
XSplit0_top_Config *lyr5_cfg;
XConvolution16_top lyr6;
XConvolution16_top_Config *lyr6_cfg;
XConvolution16_squeeze_pooling17_top lyr7;
XConvolution16_squeeze_pooling17_top_Config *lyr7_cfg;
XPooling17_top lyr8;
XPooling17_top_Config *lyr8_cfg;
XRelu18_top lyr9;
XRelu18_top_Config *lyr9_cfg;
XRelu18_squeeze_innerproduct2_top lyr10;
XRelu18_squeeze_innerproduct2_top_Config *lyr10_cfg;
XInnerproduct2_top lyr11;
XInnerproduct2_top_Config *lyr11_cfg;
XInnerproduct2_squeeze_split1_top lyr12;
XInnerproduct2_squeeze_split1_top_Config *lyr12_cfg;
XSplit1_top lyr13;
XSplit1_top_Config *lyr13_cfg;
XGreater24_top lyr14;
XGreater24_top_Config *lyr14_cfg;
XBrn_exit_top lyr15;
XBrn_exit_top_Config *lyr15_cfg;
XConvolution28_top lyr16;
XConvolution28_top_Config *lyr16_cfg;
XConvolution28_squeeze_pooling29_top lyr17;
XConvolution28_squeeze_pooling29_top_Config *lyr17_cfg;
XPooling29_top lyr18;
XPooling29_top_Config *lyr18_cfg;
XPooling29_squeeze_relu3_top lyr19;
XPooling29_squeeze_relu3_top_Config *lyr19_cfg;
XRelu3_top lyr20;
XRelu3_top_Config *lyr20_cfg;
XConvolution31_top lyr21;
XConvolution31_top_Config *lyr21_cfg;
XConvolution31_squeeze_pooling32_top lyr22;
XConvolution31_squeeze_pooling32_top_Config *lyr22_cfg;
XPooling32_top lyr23;
XPooling32_top_Config *lyr23_cfg;
XRelu33_top lyr24;
XRelu33_top_Config *lyr24_cfg;
XRelu33_squeeze_innerproduct35_top lyr25;
XRelu33_squeeze_innerproduct35_top_Config *lyr25_cfg;
XInnerproduct35_top lyr26;
XInnerproduct35_top_Config *lyr26_cfg;

// sd file system from example
FATFS fatfs;
static char input_file[20] = "i0.bin"; //NOTE 20 seems to be max allowed
static char output_file[20] = "o0.bin";
static char *sd_in;
static char *sd_out;

//fcn input and outpt data sample sizes
#define INPUT_SIZE 784
#define OUTPUT_SIZE 10
#define BATCH_SIZE 1024

#define SIZE_IN INPUT_SIZE*BATCH_SIZE
#define SIZE_OUT OUTPUT_SIZE*BATCH_SIZE

uint32_t in_stream[SIZE_IN]; //use ap_fixed type

//DMA addresses (from yt example)
#define MEM_BASE_ADDR 0x01000000
#define RX_BUFF_BASE (MEM_BASE_ADDR + 0x00100000)

// *************** initialisation ****************

void initPeriph() {
    //initialising dma
    xil_printf("Initialising dma\n\r");
    axiDMA_cfg = XAxiDma_LookupConfig(XPAR_AXIDMA_0_DEVICE_ID);
    if (axiDMA_cfg) {
            int status = XAxiDma_CfgInitialize(&axiDMA,axiDMA_cfg);
            if (status != XST_SUCCESS) {
                    xil_printf("Error initalising dma\n");
            }
    }
    //disable interrupts (from example)
    XAxiDma_IntrDisable(&axiDMA, XAXIDMA_IRQ_ALL_MASK, XAXIDMA_DEVICE_TO_DMA);
    XAxiDma_IntrDisable(&axiDMA, XAXIDMA_IRQ_ALL_MASK, XAXIDMA_DMA_TO_DEVICE);

    //initialising sd
    FRESULT rc;

    rc = f_mount(&fatfs,"",1);
    if (rc) {
            xil_printf(" ERROR : f_mount returned %d\r\n", rc);
            return XST_FAILURE;
    }

    
    xil_printf("Initialising fpgaconvnet layer0\n\r");
    lyr0_cfg = XBrn_se_conf_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_BRN_SE_CONF_DEVICE_ID);
    if (lyr0_cfg) {
        int status = XBrn_se_conf_top_CfgInitialize(&lyr0, lyr0_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :0:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer1\n\r");
    lyr1_cfg = XConvolution13_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_CONVOLUTION13_DEVICE_ID);
    if (lyr1_cfg) {
        int status = XConvolution13_top_CfgInitialize(&lyr1, lyr1_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :1:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer2\n\r");
    lyr2_cfg = XPooling14_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_POOLING14_DEVICE_ID);
    if (lyr2_cfg) {
        int status = XPooling14_top_CfgInitialize(&lyr2, lyr2_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :2:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer3\n\r");
    lyr3_cfg = XPooling14_squeeze_relu15_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_POOLING14_SQUEEZE_RELU15_DEVICE_ID);
    if (lyr3_cfg) {
        int status = XPooling14_squeeze_relu15_top_CfgInitialize(&lyr3, lyr3_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :3:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer4\n\r");
    lyr4_cfg = XRelu15_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_RELU15_DEVICE_ID);
    if (lyr4_cfg) {
        int status = XRelu15_top_CfgInitialize(&lyr4, lyr4_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :4:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer5\n\r");
    lyr5_cfg = XSplit0_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_SPLIT0_DEVICE_ID);
    if (lyr5_cfg) {
        int status = XSplit0_top_CfgInitialize(&lyr5, lyr5_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :5:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer6\n\r");
    lyr6_cfg = XConvolution16_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_CONVOLUTION16_DEVICE_ID);
    if (lyr6_cfg) {
        int status = XConvolution16_top_CfgInitialize(&lyr6, lyr6_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :6:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer7\n\r");
    lyr7_cfg = XConvolution16_squeeze_pooling17_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_CONVOLUTION16_SQUEEZE_POOLING17_DEVICE_ID);
    if (lyr7_cfg) {
        int status = XConvolution16_squeeze_pooling17_top_CfgInitialize(&lyr7, lyr7_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :7:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer8\n\r");
    lyr8_cfg = XPooling17_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_POOLING17_DEVICE_ID);
    if (lyr8_cfg) {
        int status = XPooling17_top_CfgInitialize(&lyr8, lyr8_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :8:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer9\n\r");
    lyr9_cfg = XRelu18_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_RELU18_DEVICE_ID);
    if (lyr9_cfg) {
        int status = XRelu18_top_CfgInitialize(&lyr9, lyr9_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :9:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer10\n\r");
    lyr10_cfg = XRelu18_squeeze_innerproduct2_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_RELU18_SQUEEZE_INNERPRODUCT2_DEVICE_ID);
    if (lyr10_cfg) {
        int status = XRelu18_squeeze_innerproduct2_top_CfgInitialize(&lyr10, lyr10_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :10:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer11\n\r");
    lyr11_cfg = XInnerproduct2_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_INNERPRODUCT2_DEVICE_ID);
    if (lyr11_cfg) {
        int status = XInnerproduct2_top_CfgInitialize(&lyr11, lyr11_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :11:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer12\n\r");
    lyr12_cfg = XInnerproduct2_squeeze_split1_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_INNERPRODUCT2_SQUEEZE_SPLIT1_DEVICE_ID);
    if (lyr12_cfg) {
        int status = XInnerproduct2_squeeze_split1_top_CfgInitialize(&lyr12, lyr12_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :12:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer13\n\r");
    lyr13_cfg = XSplit1_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_SPLIT1_DEVICE_ID);
    if (lyr13_cfg) {
        int status = XSplit1_top_CfgInitialize(&lyr13, lyr13_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :13:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer14\n\r");
    lyr14_cfg = XGreater24_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_GREATER24_DEVICE_ID);
    if (lyr14_cfg) {
        int status = XGreater24_top_CfgInitialize(&lyr14, lyr14_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :14:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer15\n\r");
    lyr15_cfg = XBrn_exit_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_BRN_EXIT_DEVICE_ID);
    if (lyr15_cfg) {
        int status = XBrn_exit_top_CfgInitialize(&lyr15, lyr15_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :15:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer16\n\r");
    lyr16_cfg = XConvolution28_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_CONVOLUTION28_DEVICE_ID);
    if (lyr16_cfg) {
        int status = XConvolution28_top_CfgInitialize(&lyr16, lyr16_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :16:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer17\n\r");
    lyr17_cfg = XConvolution28_squeeze_pooling29_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_CONVOLUTION28_SQUEEZE_POOLING29_DEVICE_ID);
    if (lyr17_cfg) {
        int status = XConvolution28_squeeze_pooling29_top_CfgInitialize(&lyr17, lyr17_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :17:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer18\n\r");
    lyr18_cfg = XPooling29_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_POOLING29_DEVICE_ID);
    if (lyr18_cfg) {
        int status = XPooling29_top_CfgInitialize(&lyr18, lyr18_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :18:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer19\n\r");
    lyr19_cfg = XPooling29_squeeze_relu3_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_POOLING29_SQUEEZE_RELU3_DEVICE_ID);
    if (lyr19_cfg) {
        int status = XPooling29_squeeze_relu3_top_CfgInitialize(&lyr19, lyr19_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :19:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer20\n\r");
    lyr20_cfg = XRelu3_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_RELU3_DEVICE_ID);
    if (lyr20_cfg) {
        int status = XRelu3_top_CfgInitialize(&lyr20, lyr20_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :20:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer21\n\r");
    lyr21_cfg = XConvolution31_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_CONVOLUTION31_DEVICE_ID);
    if (lyr21_cfg) {
        int status = XConvolution31_top_CfgInitialize(&lyr21, lyr21_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :21:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer22\n\r");
    lyr22_cfg = XConvolution31_squeeze_pooling32_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_CONVOLUTION31_SQUEEZE_POOLING32_DEVICE_ID);
    if (lyr22_cfg) {
        int status = XConvolution31_squeeze_pooling32_top_CfgInitialize(&lyr22, lyr22_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :22:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer23\n\r");
    lyr23_cfg = XPooling32_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_POOLING32_DEVICE_ID);
    if (lyr23_cfg) {
        int status = XPooling32_top_CfgInitialize(&lyr23, lyr23_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :23:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer24\n\r");
    lyr24_cfg = XRelu33_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_RELU33_DEVICE_ID);
    if (lyr24_cfg) {
        int status = XRelu33_top_CfgInitialize(&lyr24, lyr24_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :24:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer25\n\r");
    lyr25_cfg = XRelu33_squeeze_innerproduct35_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_RELU33_SQUEEZE_INNERPRODUCT35_DEVICE_ID);
    if (lyr25_cfg) {
        int status = XRelu33_squeeze_innerproduct35_top_CfgInitialize(&lyr25, lyr25_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :25:\n\r");
        }
    }

    xil_printf("Initialising fpgaconvnet layer26\n\r");
    lyr26_cfg = XInnerproduct35_top_LookupConfig(XPAR_BRN_SE_CONF_NETWORK_INNERPRODUCT35_DEVICE_ID);
    if (lyr26_cfg) {
        int status = XInnerproduct35_top_CfgInitialize(&lyr26, lyr26_cfg);
        if (status != XST_SUCCESS) {
            xil_printf("Error initalising layer :26:\n\r");
        }
    }

    return XST_SUCCESS;
}

// *************** sd card functions ****************

int sd_read( void* dest_addr) {
    FIL fil;
    FRESULT rc;
    uint length = 0;
    uint bytes_read = 0;
    sd_in = (char *)input_file;
    u32 byte_len = SIZE_IN * sizeof(uint32_t);
    //open file to read
    rc = f_open(&fil, sd_in, FA_READ);
    if (rc) {
            xil_printf(" ERROR : %s f_open returned %d\r\n", sd_in, rc);
            return XST_FAILURE;
    }
    // get length of file
    length=f_size(&fil);
    //pointer to beginning of file
    rc = f_lseek(&fil, 0);
    if (rc) {
            xil_printf(" ERROR : %s f_lseek returned %d\r\n", sd_in, rc);
            return XST_FAILURE;
    }
    //file obj, address to read into, file size, number of bytes actually read
    rc = f_read(&fil, dest_addr, length, &bytes_read);
    if (rc) {
            xil_printf(" ERROR : %s f_read returned %d\r\n", sd_in, rc);
            return XST_FAILURE;
    }

    //check if bytes read equals to expected number of bytes
    if((bytes_read != byte_len)&&(byte_len != 0)) {
            xil_printf(" ERROR: File: '%s', Expected size: %d; Actual size: %d\r\n", sd_in, byte_len, bytes_read);
            return XST_FAILURE;
    }
    //close the file
    rc = f_close(&fil);
    if (rc) {
            xil_printf(" ERROR : %s f_close returned %d\r\n", sd_in, rc);
            return XST_FAILURE;
    }
    //if (FPGACONVNET_DEBUG) {
    //	xil_printf("(DEBUG) SD card: File '%s' read. Length: %d; Addr.: 0x%08x\r\n", sd_in, length, dest_addr);
    //}
    return XST_SUCCESS;
}

int sd_write(u32* start_addr) {
    FIL fil;
    FRESULT rc;
    uint length;
    sd_out = (char *)output_file;
    u32 byte_len = SIZE_OUT * sizeof(uint32_t);
    rc = f_open(&fil, sd_out, FA_CREATE_ALWAYS | FA_WRITE);
    if (rc) {
        xil_printf(" ERROR : %s f_open returned %d\r\n", sd_out, rc);
        return XST_FAILURE;
    }
    //length=file_size(&fil);
    rc = f_lseek(&fil, 0);
    if (rc) {
        xil_printf(" ERROR : %s f_lseek returned %d\r\n", sd_out, rc);
        return XST_FAILURE;
    }
    rc = f_write(&fil, start_addr, byte_len, &length);
    if (rc) {
        xil_printf(" ERROR : %s f_write returned %d\r\n", sd_out, rc);
        return XST_FAILURE;
    }
    if(length != byte_len) {
        xil_printf("Expected written bytes: %d. Written bytes: %d\r\n", byte_len, length);
        return XST_FAILURE;
    }
    rc = f_close(&fil);
    if (rc) {
        xil_printf(" ERROR : %s f_close returned %d\r\n", sd_out, rc);
        return XST_FAILURE;
    }
    //if (FPGACONVNET_DEBUG) {
    //    xil_printf("(DEBUG) SD card: File '%s' written. Length: %d\r\n", sd_out, length);
    //}
    return XST_SUCCESS;
}

// *************************** MAIN ******************************

int main() {
    init_platform();
    print("Hello World\n\r");

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
    /*uint32_t data;
	for (int idx=0;idx<SIZE_IN;idx++) {
		data = idx % 16;
		in_stream[idx] = data;
	}*/

    // ****************** starting core *****************
    xil_printf("Starting Core\n\r");

    //start fcn blocks
    XBrn_se_conf_top_Start(&lyr0);
    XConvolution13_top_Start(&lyr1);
    XPooling14_top_Start(&lyr2);
    XPooling14_squeeze_relu15_top_Start(&lyr3);
    XRelu15_top_Start(&lyr4);
    XSplit0_top_Start(&lyr5);
    XConvolution16_top_Start(&lyr6);
    XConvolution16_squeeze_pooling17_top_Start(&lyr7);
    XPooling17_top_Start(&lyr8);
    XRelu18_top_Start(&lyr9);
    XRelu18_squeeze_innerproduct2_top_Start(&lyr10);
    XInnerproduct2_top_Start(&lyr11);
    XInnerproduct2_squeeze_split1_top_Start(&lyr12);
    XSplit1_top_Start(&lyr13);
    XGreater24_top_Start(&lyr14);
    XBrn_exit_top_Start(&lyr15);
    XConvolution28_top_Start(&lyr16);
    XConvolution28_squeeze_pooling29_top_Start(&lyr17);
    XPooling29_top_Start(&lyr18);
    XPooling29_squeeze_relu3_top_Start(&lyr19);
    XRelu3_top_Start(&lyr20);
    XConvolution31_top_Start(&lyr21);
    XConvolution31_squeeze_pooling32_top_Start(&lyr22);
    XPooling32_top_Start(&lyr23);
    XRelu33_top_Start(&lyr24);
    XRelu33_squeeze_innerproduct35_top_Start(&lyr25);
    XInnerproduct35_top_Start(&lyr26);

    //flush buffer caches?
    Xil_DCacheFlushRange((u32)in_stream, SIZE_IN*sizeof(uint32_t));
    Xil_DCacheFlushRange((u32)m_dma_buff_rx, SIZE_OUT*sizeof(uint32_t));

    //start timer
    //XScuTimer_Start(&timer);
    XTime tStart, tEnd;
    double elapsedTime, diff;

    //setting up simple dma transfers
    //xil_printf("Receive command for DMA\n\r");
    XAxiDma_SimpleTransfer(&axiDMA, (u32) m_dma_buff_rx, SIZE_OUT * sizeof(uint32_t), XAXIDMA_DEVICE_TO_DMA);
    //xil_printf("Send command for DMA\n\r");

    XAxiDma_SimpleTransfer(&axiDMA, (u32) in_stream, SIZE_IN * sizeof(uint32_t), XAXIDMA_DMA_TO_DEVICE);

    //start timer
    XTime_GetTime(&tStart);
    //check when dma has finished - total time from ddr -> core -> ddr
    while (XAxiDma_Busy(&axiDMA, XAXIDMA_DEVICE_TO_DMA) || XAxiDma_Busy(&axiDMA, XAXIDMA_DMA_TO_DEVICE));
    //stop timer
    XTime_GetTime(&tEnd);

    diff = 2.0 * (tEnd - tStart);
    //elapsed time calculated in us
    elapsedTime = 1000000*(tEnd-tStart)/(COUNTS_PER_SECOND);

    xil_printf("Output took %llu clock cycles.\n\r", diff);
    xil_printf("DMA transactions finished. Timer: %.2f us\n\r",elapsedTime);

    //invalidate cache to avoid reading rubbish (shouldnt be needed since disabled)
    //Xil_DCacheInvalidateRange((u32) m_dma_buff_rx, SIZE_OUT * sizeof(uint32_t));

    //write finished data to .bin file
    sd_write(m_dma_buff_rx);

    xil_printf("done write\n\r");

    cleanup_platform();
    return 0;
}
