import time, chardet, openai, subprocess, os, pandas as pd
from utilities.readInfo import read_info
from utilities.embedding import get_embedding
from utilities.create_clone import create_clone, get_clone_filepath
from utilities.str2float import str2float
from utilities.logger import log, clear_logs
from utilities.AskGPT import AskGPT

text_file = open("API_key.txt", "r")
openai.api_key = text_file.read()
text_file.close()

fs = pd.DataFrame()


def get_diff(old_file_path, new_file_path):
    result = subprocess.run(["diff", old_file_path, new_file_path], capture_output=True, text=True)
    return result.stdout


def summarize_str(filename, file_contents):
    prompt = "File " + filename + " has " + file_contents
    system_message = "Summarize what this file in the codebase does, assume context when neccessary."
    return AskGPT(model="gpt-3.5-turbo", system_message=system_message, prompt=prompt, temperature=0, max_tokens=256)


def sumarize(filename):
    root = read_info()
    with open(os.path.join(root, filename), 'rb') as f:
        result = chardet.detect(f.read())
    if not (result['encoding'] == 'ascii' or result['encoding'] == 'ISO-8859-1'):
        print("File " + filename + " was not summarised as it is not a text file")
        return "Ignore"
    full_file_path = os.path.join(root, filename)
    with open(full_file_path, 'r') as f:
        file_contents = f.read()

    return summarize_str(filename, file_contents)


def syncAI(sync_flag):
    path = read_info()
    global fs
    fsfilename = "AIFiles/" "fs_" + path.split('/')[-1] + ".csv"

    fs = pd.read_csv(fsfilename)
    fs['embedding'] = fs.embedding.apply(lambda x: str2float(str(x)))

    file_paths_details = []
    Files_to_ignore = open(path + "/.AIIgnore", "r").read().splitlines()
    # print("Files and directories to ignore:")
    # print(Files_to_ignore)

    for root, directories, files in os.walk(path):
        # Exclude any directories that appear in the ignore list
        directories[:] = [d for d in directories if d not in Files_to_ignore]
        # print("Directories:", directories)
        for filename in files:
            # print("File : "+filename)
            if os.path.relpath(os.path.join(root, filename), path) not in Files_to_ignore:
                # Append relative path to file to file_paths_details list
                file_paths_details.append(os.path.relpath(os.path.join(root, filename), path))

    for file in file_paths_details:
        clone_path = get_clone_filepath(path, file)
        # print("File : "+file)
        # print("Clone Path : "+clone_path)
        if get_diff(os.path.join(path, file), clone_path) != "":
            print("File " + file + " has changed")
            log("File " + file + " has changed. Syncing AI...")
            fs.loc[fs["file_path"] == file, "summary"] = sumarize(file)
            time.sleep(20)
            fs.loc[fs["file_path"] == file, "embedding"] = None

    for ind in fs.index:
        if (fs['embedding'][ind] == None):
            fs['embedding'][ind] = get_embedding(fs['summary'][ind], 0.5)

            print(type(fs.loc[fs["file_path"] == file, "summary"]))
            # print(type(get_embedding( fs.loc[fs["file_path"] == file, "summary"],0)))

    # Find the set difference between file_paths_details and df4["filepath"]

    new_file_paths = set(file_paths_details) - set(fs["file_path"])
    if len(new_file_paths) > 0:
        print("New Files : " + str(len(new_file_paths)))
        log("New Files : " + str(len(new_file_paths)))
        if (sync_flag == 0):
            clear_logs()
            return "NEW", list(new_file_paths)

    # Iterate over the new_file_paths set and create a new row for each file path
    new_rows = []
    for file_path in new_file_paths:
        # Create a dictionary with the values for each column in the new row
        row_dict = {
            "file_path": file_path
            # Add any other columns you need for the new row
        }
        # Append the new row to the new_rows list
        new_rows.append(row_dict)
        print("New File : " + file_path)

    # Convert the new_rows list of dictionaries to a pandas DataFrame
    new_fs = pd.DataFrame(new_rows)
    del_file_paths = set(fs["file_path"]) - set(file_paths_details)

    # Iterate over the del_file_paths set and remove the corresponding rows from dataframes
    for file_path in del_file_paths:
        fs = fs[fs["file_path"] != file_path]
        print("Deleted File : " + str(file_path))

    new_fs['embedding'] = ''
    new_fs['summary'] = ''
    for ind in new_fs.index:
        log("Analyzing New File : " + new_fs['file_path'][ind])
        new_fs['summary'][ind] = sumarize(new_fs['file_path'][ind])
        time.sleep(20)
        if (new_fs['summary'][ind] != "Ignore"):
            new_fs['embedding'][ind] = get_embedding(new_fs['summary'][ind], 0.5)

    fs = pd.concat([fs, new_fs], ignore_index=True)

    fs.to_csv(fsfilename, index=False)

    create_clone(read_info())
    clear_logs()
    return "DONE", list(new_file_paths)
