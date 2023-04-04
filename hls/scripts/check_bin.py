import sys
import parser
import argparse
import numpy as np
import os

sys.path.append(os.environ.get("FPGACONVNET_HLS"))

try:
    from tools.onnx_data import ONNXData, validate_output
except ModuleNotFoundError:
    from onnx_data import ONNXData, validate_output


# NOTE function for parsing multiple path inputs
def dir_path(str_path: str):
    for quote in ['"', "'"]:
        if str_path.startswith(quote):
            str_path = str_path[1:-1]
    if str_path.startswith('~'):
        str_path = os.path.expanduser(str_path)
    if os.path.exists(str_path):
        return str_path
    raise NotADirectoryError(str_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for comparing sample binary files")
    parser.add_argument('-gp', '--gold_path',required=True,
            type=dir_path,
            nargs="+",
            help='Path to golden data generated from onnx (.bin)')

    parser.add_argument('-ap', '--actual_path',metavar='PATH',required=True,
            help='Path to actual board-generated data (.bin)')
    parser.add_argument('-dw', '--data_width',required=False,type=int,default=16,
            help='Number of bits')
    parser.add_argument('-e', '--error_tolerance',required=False,type=float,default=0.2,
            help='Allowable error between gold and actual data')
    parser.add_argument('-v', '--verbose',required=False,action='store_true',
            help='Print a whole lot of stuff')
    parser.add_argument('-ee', '--early_exit',required=False,action='store_true',
            help='Switch to EE version with 16bit upper as sample ID, 16 bit lower')

    #TODO add custom fixed point precision split, defaulting to 8,8

    args = parser.parse_args()

    validate_output(args)
