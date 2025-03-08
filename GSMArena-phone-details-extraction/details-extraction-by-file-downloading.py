import os
path = "Enter Your Location"
os.chdir(path)
def read_text_file(file_path): 
    with open(file_path, 'r') as f: 
        for i in f:
            try:
                if 'modelname' in i:
                    print(i[69:-6],end='@')
                if 'link-network-detail' in i:
                    print(i[i.find('>',49)+1:-10],end='@')
                if '"status"' in i:
                    print(i[35:-6],end='@')
                if 'dimensions' in i:
                    print(i[40:-6])
                    return
            except:
                pass
try:
    for file in os.listdir(): 
        if file.endswith(".html"): 
            file_path = f"{path}\{file}"
            read_text_file(file_path)
except:pass
