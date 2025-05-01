#!/bin/bash
TEST_TYPE=all

while getopts ":l:n:cseih" opt; do
    case ${opt} in
        l )
            LAYER=$OPTARG
            ;;
        n )
            TEST_NUM=$OPTARG
            ;;
        c )
            # c simulation
            TEST_TYPE=sim
            ;;
        s )
            # synthesis
            TEST_TYPE=synth
            ;;
        e )
            # co-simulation
            TEST_TYPE=cosim
            ;;
        i )
            # implementation
            TEST_TYPE=impl
            ;;
        a )
            # implementation
            TEST_TYPE=all
            ;;
        h )
            echo "USAGE: run_test.sh [-l (layer)] [-n (test number)] [-c,-s,-e,-i,-a]"
            echo "  -c = C simulation"
            echo "  -s = Synthesis"
            echo "  -e = Co-simulation"
            echo "  -i = Implementation"
            echo "  -a = All"
            exit
            ;;
    esac
done
shift $((OPTIND -1))

# Move to folder
cd $LAYER

if [ $TEST_NUM ]; then

  echo "RUNNING TEST ${TEST_NUM}"
  # GENERATE INPUTS
  mkdir -p data/test_${TEST_NUM}
  python gen_layer.py -c config/config_${TEST_NUM}.json -o $FPGACONVNET_HLS/test/layers/$LAYER/data/test_${TEST_NUM} -s src/ -h include/ -t tb/
  # RUN TEST
  vivado_hls -f $FPGACONVNET_HLS/scripts/run_hls.tcl "_  -num ${TEST_NUM} -type ${TEST_TYPE} -name ${LAYER} -layer_flag -fpga xc7z045ffg900-2 -fast"

# GENERATE REPORTS
python ../report.py -l $LAYER -n $TEST_NUM

else

  # NUMBER OF TESTS
  NUM_TEST="$(ls config/ -1U | wc -l)"
  # ITERATE OVER TESTS
  for i in $( seq 0 $(($NUM_TEST-1)) )
  do
      echo "RUNNING TEST ${i}"
      # GENERATE INPUTS
      mkdir -p data/test_${i}
      python gen_layer.py -c config/config_${i}.json -o $FPGACONVNET_HLS/test/layers/$LAYER/data/test_${i} -s src/ -h include/ -t tb/
      # RUN TEST
      vivado_hls -f $FPGACONVNET_HLS/scripts/run_hls.tcl "_  -num ${i} -type ${TEST_TYPE} -name ${LAYER} -layer_flag -fpga xc7z045ffg900-2 -fast"
  done

# GENERATE REPORTS
python ../report.py -l $LAYER
fi
