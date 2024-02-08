#!/bin/bash
destination=$1

scp -i ~/.ssh/id_rsa modules/accum/logs/*           $destination:~/fpgaconvnet-hls/runs/modules/accum/logs/
scp -i ~/.ssh/id_rsa modules/conv/logs/*            $destination:~/fpgaconvnet-hls/runs/modules/conv/logs/
scp -i ~/.ssh/id_rsa modules/fork/logs/*            $destination:~/fpgaconvnet-hls/runs/modules/fork/logs/
scp -i ~/.ssh/id_rsa modules/glue/logs/*            $destination:~/fpgaconvnet-hls/runs/modules/glue/logs/
scp -i ~/.ssh/id_rsa modules/relu/logs/*            $destination:~/fpgaconvnet-hls/runs/modules/relu/logs/
scp -i ~/.ssh/id_rsa modules/pool/logs/*            $destination:~/fpgaconvnet-hls/runs/modules/pool/logs/
scp -i ~/.ssh/id_rsa modules/sliding_window/logs/*  $destination:~/fpgaconvnet-hls/runs/modules/sliding_window/logs/
