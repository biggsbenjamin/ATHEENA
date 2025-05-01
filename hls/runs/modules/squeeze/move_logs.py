import os
import json
import shutil

def main(filepath):
    result_files = os.listdir(filepath)
    mv_count=0
    for result_file in result_files:
        if result_file.endswith(".json"):
            try:
                fn = f"{filepath}/{result_file}"
                new_fn = f"strange_logs/{result_file}"
                with open(fn,"r") as f:
                    tmp = json.load(f)
                    if int(tmp["resources"]["LUT"]) == 4605 and \
                            int(tmp["resources"]["FF"]) == 6533:
                        #move file to logs
                        shutil.move(fn, new_fn)
                        mv_count+=1

            except:
                print(f"Cannot open {result_file}")
    print(f"Files available:{len(result_files)}, {mv_count}")

    return

if __name__ == "__main__":
    main("./logs/")
