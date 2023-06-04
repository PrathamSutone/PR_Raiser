import pandas as pd, json, os, chardet, openai, time
from utilities.embedding import split_embed
from utilities.create_clone import create_clone
from utilities.files2analyze import files2analyze
from utilities.tokenCount import tokenCount
from utilities.keyutils import get_key
from utilities.rates import get_rates

def summarize_str(filename, string, email, userlogger):
    openai.api_key = get_key(email)
    while True:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system",
                           "content": "Summarize what this file in the codebase does, assume context when neccessary."},
                          {"role": "user", "content": "File " + filename + " has " + string}],
                temperature=0,
                max_tokens=256
            )
            return response["choices"][0]["message"]['content']
        except Exception as e:
            userlogger.log(f"Encountered error: {e}")
            userlogger.log("Retrying in 20 seconds...")
            time.sleep(20)

def summarize_file(file, i, userlogger, email):
    with open(file, 'rb') as f:
        result = chardet.detect(f.read())
    if not (result['encoding'] == 'ascii' or result['encoding'] == 'ISO-8859-1'):
        p = ("File " + file + " was not Analyzed as it is not a text file")
        userlogger.log(p)
        return i, "Ignore"
    i += 1
    p = ("Analyzing " + file)
    userlogger.log(p)
    with open(file, 'r') as f:
        try:
            file_contents = f.read()
        except UnicodeDecodeError:
            p = ("File " + file + " was not Analyzed as it is not a text file")
            userlogger.log(p)
            return i, "Ignore"

    if tokenCount(file_contents) > 3400:
        p = ("File " + file + " was not analyzed as it is too long")
        userlogger.log(p)

        return i, "File content too long"
    return i, summarize_str(file, file_contents, email, userlogger)


def train_AI(path, userlogger, email):

    fsfilename = "user/" + email+'/AIFiles/'+ path.split('/')[-1] + ".csv"

    file_paths_details = files2analyze(path.split('/')[-1], email)

    if len(file_paths_details) == 0:
        userlogger.log("No files detected")
        userlogger.log("Please Add files in the project and train again")
        userlogger.log("Tip : Start with a ReadME.md")
        time.sleep(5)
        return

    fs = pd.DataFrame(file_paths_details)
    fs.columns = ['file_path']
    start_time = time.time()
    chat_limit = get_rates(email).split(",")[0]
    delay = 60 / int(chat_limit)
    i = 0
    fs['summary'] = ''
    fs['embedding'] = ''
    userlogger.log("Starting analysis")

    for ind in fs.index:
        i_new, fs['summary'][ind] = summarize_file(fs['file_path'][ind], i,userlogger,email)
        if fs['summary'][ind] != "Ignore":
            fs['embedding'][ind] = split_embed(fs['summary'][ind],email)
        if i_new != i:
            time.sleep(delay)
            i = i_new
        if i != 0:
            rate = 60 * i / (time.time() - start_time)
            time_elapsed = time.time() - start_time
            p = (str(round(100 * (ind + 1) / len(fs))) + "% done. Rate: " + str(
                round(rate, 2)) + " requests/min. Time Elapsed: " + str(round(time_elapsed / 60, 2)))
            print(p)
            userlogger.log(p)
            if rate > int(chat_limit):
                delay = delay + 0.2
                # print("Rate limit reached. Delay increased to " + str(delay) + " seconds")
            if rate < 0.9 * int(chat_limit):
                delay = delay * 0.8
                # print("Rate limit not reached. Delay decreased to " + str(delay) + " seconds")

    fs = fs[fs['summary'] != "Ignore"]

    userlogger.log("Analyzed all files successfully")


    fs.to_csv(fsfilename, index=False)

    print("100% Done")
    userlogger.clear_logs()
    create_clone(path, email)
    userlogger.log("-----------------------------------------------------")
    userlogger.log("***")
    userlogger.log("Your repo was trained into the AI successfully")
    userlogger.log("***")
    userlogger.log("-----------------------------------------------------")
    time.sleep(200)
    userlogger.clear_logs()
    return
