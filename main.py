from flask import Flask, send_file, send_from_directory, request
from werkzeug.utils import secure_filename

import subprocess
import random  
import string 
import tempfile
import tarfile

class CompileError(ValueError):
    pass

def get_random_filename(length=15):
    result = ''.join((random.choice(string.ascii_lowercase) for x in range(length)))
    return result

app = Flask(__name__)



def asm2obj(filename, objname):
    command = ["mips-linux-gnu-as"] 
    command += ["-g2", "-g", "--gdwarf2", "-mips32", "-o", objname, filename]
    proc = subprocess.run(command, capture_output=True)
    if proc.returncode != 0:
        raise CompileError(str(proc.stderr, encoding="utf8"))

def obj2data(objname, dataname):
    command = ["mips-linux-gnu-objdump"]
    command += ["--full-contents",  objname]
    command += ["-j", ".data"]
    proc = subprocess.run(command, capture_output=True)
    
    if proc.returncode != 0:
        raise CompileError(str(proc.stderr, encoding="utf8"))
    
    lines = parse_full_contents(str(proc.stdout, encoding="utf8"))
    with open(dataname, "w") as f:
        f.write("\n".join(lines))

def obj2text(objname, dataname):
    command = ["mips-linux-gnu-objdump"]
    command += ["--full-contents",  objname]
    command += ["-j", ".text", "-O0"]
    proc = subprocess.run(command, capture_output=True)
    
    if proc.returncode != 0:
        raise CompileError(str(proc.stderr, encoding="utf8"))
    lines = parse_full_contents(str(proc.stdout, encoding="utf8"))
    with open(dataname, "w") as f:
        f.write("\n".join(lines))

def obj2commented(objname, commentedversion=None):
    command = ["mips-linux-gnu-objdump"]
    command += ["-S",  objname]
    command += ["-j", ".text", "--source-comment=##  "]
    proc = subprocess.run(command, capture_output=True)
    
    if proc.returncode != 0:
        raise CompileError(str(proc.stderr, encoding="utf8"))
    if commentedversion:
        with open(commentedversion, "wb") as f:
            f.write(proc.stdout)
    else:
        return str(proc.stdout, encoding="utf8")

def parse_full_contents(text):
    res = []
    parsing = False
    for line in text.split("\n"):
        if "Contents of section" in line:
            parsing = True
            continue
        if parsing and len(line) > 0:
            line = line.strip()
            pieces = line.split(" ")
            address = int(pieces[0], base=16)
            for i in range(4):
                res.append("%08x %s" % ((address+i*4, pieces[i+1])))
    return res

@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/favicon.ico")
def favicon():
    return send_file("favicon.ico")

@app.route("/api/compile", methods=["POST"])
def api_compile():
    with tempfile.TemporaryDirectory() as tmpdirname:
        code = request.form["code"]
        sourcefile = f"{tmpdirname}/program.asm"
        with open(sourcefile, "w") as f:
            f.write(code)
        objfile = f"{tmpdirname}/program.o"
        
        try:
            asm2obj(sourcefile, objfile)
        except Exception as e:
            return {
                "error": str(e)
            }

        command = ["mips-linux-gnu-objdump"]
        command += ["--full-contents",  objfile]
        command += ["-j", ".data", "-d"]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            return {
                "error": str(stdout, encoding="utf8") + str(stderr, encoding="utf8")
            }

        proc = subprocess.Popen(["python3", "parser.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate(input=stdout)
        data = str(stdout, encoding="utf8")

        command = ["mips-linux-gnu-objdump"]
        command += ["--full-contents",  objfile]
        command += ["-j", ".text", "-d"]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            return {
                "error": str(stdout, encoding="utf8") + str(stderr, encoding="utf8")
            }

        proc = subprocess.Popen(["python3", "parser.py"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate(input=stdout)
        text = str(stdout, encoding="utf8")

        command = ["mips-linux-gnu-objdump"]
        command += ["-S",  objfile, "--source-comment=##  "]
        command += ["-j", ".text"]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            return {
                "error": str(stdout, encoding="utf8") + str(stderr, encoding="utf8")
            }
        text_with_source = str(stdout, encoding="utf8")
        return {
            "data": data,
            "text": text,
            "text_with_source": text_with_source
        }

@app.route('/api/compile_zip', methods=["POST"])
def api_compile_zip():
    with tempfile.TemporaryDirectory() as tmpdirname:
        file = request.files['file']
        asm_filename = f"{tmpdirname}/programa.asm"
        file.save(asm_filename)
        obj_filename = f"{tmpdirname}/programa.o"
        data_filename = f"{tmpdirname}/datos"
        text_filename = f"{tmpdirname}/instrucciones"
        commented_filename = f"{tmpdirname}/programa.lst"
        asm2obj(asm_filename, obj_filename)

        obj2data(obj_filename, data_filename)
        obj2text(obj_filename, text_filename)
        obj2commented(obj_filename, commented_filename)
        tar_filename = f"{tmpdirname}/result.tar.gz"

        with tarfile.open(tar_filename, mode='w:gz') as z:
            z.add(data_filename, arcname=data_filename.split("/")[-1])
            z.add(text_filename, arcname=text_filename.split("/")[-1])
            z.add(commented_filename, arcname=commented_filename.split("/")[-1])

        return send_file(tar_filename)
    
@app.errorhandler(CompileError)
def compile_error(e):
    return str(e), 500
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)