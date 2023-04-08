#!/bin/bash

# parsing some arguments - want to control generation
ALL=0
LYR_ARR=()
PRT_IDX_ARG=0
GEN_TOP=0
RUN_VIVADO=0
GEN_CODE=0

while getopts "al:tvch" opt; do
    case ${opt} in
        a ) ALL=1
            GEN_TOP=1
            #RUN_VIVADO=1
            GEN_CODE=1
            ;;
        l ) set -f # disable glob
            IFS=' ' # split on space char
            LYR_ARR=($OPTARG)
            PRT_IDX_ARG=${LYR_ARR[0]} # idx0 is partition
            unset LYR_ARR[0]
            ;;
        t ) GEN_TOP=1;;
        v ) RUN_VIVADO=1
            echo "Running Vivado IP integrator"
            ;;
        c ) GEN_CODE=1
            echo "Running host code generation"
            ;;
        h )
            echo "TODO Some useful help thing... [-a (gen all layers+top)]"
            echo "[-l "arg1 arg2 arg3..."(partition:arg1, gen specific layer:arg2,3...) ]"
            echo "[-t (generate top)] [-v (run vivado integrator)]"
            echo "[-c (generate host code)]"
            exit
            ;;
    esac
done
shift $((OPTIND -1))

####################### Initialise variables ##########################
NETWORK=brn_se_test
MODEL_PATH=$FPGACONVNET_OPTIMISER/examples/models/atheena/branchy_lenet_20220902.onnx
WEIGHTS_PATH=""
PARTITION_INFO_PATH=*.json
IMAGE_PATH=$FPGACONVNET_HLS/test/data/IMAGES_ee-pc75_bs1024
ZYNQ_PART=xc7z045ffg900-2
ZYNQ_BOARD=xilinx.com:zc706:part0:1.4
#######################################################################

# move into network folder
#cd $NETWORK (already in network folder)

FREQ=125
# WARNING!!! might need to change to 64 so we have similar DMA overhead latency
PORT_WIDTH=32 #NOTE dma port width different to axis port width
WEIGHTS_RELOADING_FLAG=0 #NOTE not currently implemented
SPLIT_NETWORK_FLAG=1 #extra arg for tcl scripts
printf "Network name: ${NETWORK}\n"
printf "Target operating frequency: ${FREQ}MHz\n"

if [ $ALL -eq 1 ]
then
    # generate all the layers and top
    echo "GENERATING ALL LAYERS IN HLS + TOP BLOCK"
    # add all partitions and layers to go through
    # get the number of partitions
    NUM_PARTITIONS=$( jq '.partition | length' $PARTITION_INFO_PATH )
    p_seq=$(seq 0 $((${NUM_PARTITIONS}-1)) )
else
    # do chosen layers in chosen partition
    p_seq=$(seq ${PRT_IDX_ARG} ${PRT_IDX_ARG})
    #echo "In partition ${PRT_IDX_ARG}, generating layers: ${LYR_ARR[@]}"
fi

# create outputs folder
#mkdir -p outputs

for i in $p_seq; do

    # get current partition index
    PARTITION_INDEX=$(($i))  #$(( $i - 1 ))

    # create folders
    mkdir -p partition_${PARTITION_INDEX}
    #mkdir -p partition_${PARTITION_INDEX}/${NETWORK}_top/tb #FIXME add testing back in
    mkdir -p partition_${PARTITION_INDEX}/${NETWORK}_top/src
    mkdir -p partition_${PARTITION_INDEX}/${NETWORK}_top/include
    mkdir -p partition_${PARTITION_INDEX}/data

    if [ $ALL -eq 1 ]
    then
        #get number of layers
        NUM_LYRS=$( jq --argjson pi $PARTITION_INDEX '.partition[$pi].layers | length' $PARTITION_INFO_PATH )
        echo "number of layers $NUM_LYRS "
        l_seq=$( seq 0 $((${NUM_LYRS}-1)) )
    else
        #use layer array
        l_seq=$( seq 1 $((${#LYR_ARR[@]}+0)) )
    fi

    # create folders for each layer
    if [ $ALL -eq 1 ] || [ $((${#LYR_ARR[@]}+0)) -gt 0 ]
    then
        for j in $l_seq; do
            # get current layer index
            LYR_INDEX=$(($j + 0)) # $(( $j - 1 ))
            if [ $ALL -eq 1 ]
            then
                LYR_NAME=$( jq  -r --argjson pi $PARTITION_INDEX --argjson li $LYR_INDEX '.partition[$pi].layers[$li] | .name' $PARTITION_INFO_PATH)
            else
                LYR_NAME=${LYR_ARR[ $LYR_INDEX ]}
            fi
            #get name of each layer and create folder for compilation
            echo "layer name: $LYR_NAME " #DEBUG

            # create folders
            mkdir -p partition_${PARTITION_INDEX}/${LYR_NAME}
            mkdir -p partition_${PARTITION_INDEX}/${LYR_NAME}/src
            mkdir -p partition_${PARTITION_INDEX}/${LYR_NAME}/include
            #mkdir -p partition_${PARTITION_INDEX}/${LYR_NAME}/tb #FIXME add testing back in
        done
    fi

    # create hardware, #-sp is split layer compilation
    python $FPGACONVNET_HLS/scripts/generate_hardware.py -n $NETWORK -m $MODEL_PATH -p $PARTITION_INFO_PATH -i $PARTITION_INDEX -sp
    # format weights
    python $FPGACONVNET_HLS/scripts/format_weights.py -m $MODEL_PATH -p $PARTITION_INFO_PATH -i $PARTITION_INDEX
    # format featuremaps
    python $FPGACONVNET_HLS/scripts/format_featuremaps.py -m $MODEL_PATH -p $PARTITION_INFO_PATH -d $IMAGE_PATH -i $PARTITION_INDEX -s

    if [ $GEN_CODE -eq 1 ]
    then
        # auto generate code - currently per partition
        # NOTE not sure if network name is always used in code defs
        python $FPGACONVNET_HLS/tools/split_hw_helper.py -p $PARTITION_INFO_PATH -pi $PARTITION_INDEX gen_host_code -n ${NETWORK}
    fi

    cd partition_${PARTITION_INDEX}

    if [ $ALL -eq 1 ] || [ $((${#LYR_ARR[@]}+0)) -gt 0 ]
    then
        #TODO currently gen hw py script requires paths to exits, get rid of this so that only loop is hls gen
        #synthesise implement and export ip for each layer - checking not performed
        for k in $l_seq; do #does all layers
            # get current layer index
            LYR_INDEX=$(($k))  #$(( $i - 1 ))
            if [ $ALL -eq 1 ]
            then
                LYR_NAME=$( jq  -r --argjson pi $PARTITION_INDEX --argjson li $LYR_INDEX '.partition[$pi].layers[$li] | .name' ../${PARTITION_INFO_PATH} )
            else
                LYR_NAME=${LYR_ARR[$LYR_INDEX]}
            fi

            #run vivado hls
            cd ${LYR_NAME}
            vivado_hls -f $FPGACONVNET_HLS/scripts/run_hls.tcl "_ -name ${LYR_NAME} -fpga ${ZYNQ_PART} -split_net_flag -fast -reset -type impl"
            cd ..
        done
    fi

    ##FIXME can't get include flags to work so copying files
    mkdir -p tmp_inc

    # top level axiu (stream) to stream with less signals
    if [ $GEN_TOP -eq 1 ]
    then
        ##FIXME can't get include flags to work so copying files
        cp */include/* ./tmp_inc/

        cd ${NETWORK}_top
        vivado_hls -f $FPGACONVNET_HLS/scripts/run_hls.tcl "_ -name ${NETWORK} -fpga ${ZYNQ_PART} -split_net_flag -fast -reset -type impl"
        cd ..
    fi

    if [ $RUN_VIVADO -eq 1 ]
    then
        ################################# set up vivado hardware ################################
        printf "\n\
#################################\n\
# Running tcl scripts in Vivado #\n\
#################################\n"

        #  ( argv 0 : network name          )
        #  ( argv 1 : fpga part name        )
        #  ( argv 2 : fpga board part       )
        #  ( argv 3 : board frequency       )
        #  ( argv 4 : port width            )
        #  ( argv 5 : weights reloading on  )
        #SPLIT NETWORK
        #  ( argv 6 : split network on      )

        vivado -mode batch -notrace -source $FPGACONVNET_HLS/scripts/gen_hw.tcl \
            -tclargs    $NETWORK \
                        $ZYNQ_PART \
                        $ZYNQ_BOARD \
                        $FREQ \
                        $PORT_WIDTH \
                        $WEIGHTS_RELOADING_FLAG \
                        $SPLIT_NETWORK_FLAG
    fi

done
