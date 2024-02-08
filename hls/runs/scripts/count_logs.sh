#!/bin/bash

NUM_ACCUM=$( ls modules/accum/logs | wc -l )
NUM_CONV=$( ls modules/conv/logs | wc -l )
NUM_FORK=$( ls modules/fork/logs | wc -l )
NUM_GLUE=$( ls modules/glue/logs | wc -l )
NUM_RELU=$( ls modules/relu/logs | wc -l )
NUM_POOL=$( ls modules/pool/logs | wc -l )
NUM_SLIDING_WINDOW=$( ls modules/sliding_window/logs | wc -l )

echo "accum             : $NUM_ACCUM" 
echo "conv              : $NUM_CONV" 
echo "fork              : $NUM_FORK" 
echo "glue              : $NUM_GLUE" 
echo "relu              : $NUM_RELU" 
echo "pool              : $NUM_POOL" 
echo "sliding window    : $NUM_SLIDING_WINDOW" 
