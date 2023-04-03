import re
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]

fout = open(output_file, "w")
with open(input_file, "r") as f:
    for line in f:
        # ram = re.search("reg\ \[([0-9]+)\:0\]\ ram\ \[0\:([0-9]+)\]", line)
        # if ram:
        #     size = int(ram.group(1))*int(ram.group(2))
        #     if size > 4500:
        #         line = "(* ram_style = \"block\" *) " + line
        # mem = re.search("reg\ \[([0-9]+)\:0\]\ MEM\ \[0\:([0-9]+)\]", line)
        # if mem:
        #     size = int(mem.group(1))*int(mem.group(2))
        #     if size > 4500:
        #         line = "(* ram_style = \"block\" *) " + line
        ram = re.search("reg\ \[([0-9]+)\:0\]\ ram\ \[0\:([0-9]+)\]", line)
        if ram:
            line = "(* ram_style = \"mixed\" *) " + line
        one_big_ram = re.search("reg\ \[([0-9]+)\:0\]\ one_big_ram\ \[0\:([0-9]+)\]", line)
        if one_big_ram:
            line = "(* ram_style = \"block\" *) " + line
        # mem = re.search("reg\ \[([0-9]+)\:0\]\ MEM\ \[0\:([0-9]+)\]", line)
        # if mem:
        #     line = "(* ram_style = \"mixed\" *) " + line
        # if re.search("OpTree_[0-9]+\ adder\_tree\ ", line):
        #     line = "(* use_dsp = \"no\" *) " + line
        # if re.search("OpTree\ adder\_tree\ ", line):
        #     line = "(* use_dsp = \"no\" *) " + line
        # # fix vectorDot to infer DSP properly
        # if re.search("mac <= \$signed\(_mac_T\) \+ \$signed\(_GEN_2\)", line):
        #     line = "(* use_dsp = \"yes\" *) mac <= $signed($signed(a) * $signed(b)) + $signed(_GEN_2);\n"
        # if re.search("mac <= _mac_T_1\[31\:0\];", line):
        #     print("here")
        #     line = "(* use_dsp = \"yes\" *) mac <= $signed($signed(a) * $signed(b));\n"
        fout.write(line)
fout.close()
