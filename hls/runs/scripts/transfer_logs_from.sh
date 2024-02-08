#!/bin/bash
destination=$1

scp -i ~/.ssh/id_rsa $destination:~/fpgaconvnet-hls/runs/modules/accum/logs/*           modules/accum/logs/
scp -i ~/.ssh/id_rsa $destination:~/fpgaconvnet-hls/runs/modules/conv/logs/*            modules/conv/logs/
scp -i ~/.ssh/id_rsa $destination:~/fpgaconvnet-hls/runs/modules/fork/logs/*            modules/fork/logs/
scp -i ~/.ssh/id_rsa $destination:~/fpgaconvnet-hls/runs/modules/glue/logs/*            modules/glue/logs/
scp -i ~/.ssh/id_rsa $destination:~/fpgaconvnet-hls/runs/modules/relu/logs/*            modules/relu/logs/
scp -i ~/.ssh/id_rsa $destination:~/fpgaconvnet-hls/runs/modules/pool/logs/*            modules/pool/logs/
scp -i ~/.ssh/id_rsa $destination:~/fpgaconvnet-hls/runs/modules/sliding_window/logs/*  modules/sliding_window/logs/
