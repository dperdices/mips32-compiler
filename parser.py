# Programa de parseo (muy naive) del output de objdump
# Autor: Daniel Perdices <daniel.perdices@uam.es>

import sys

starts_code = False
for line in sys.stdin:
    if line.startswith("00000000"):
        starts_code = True
    if starts_code:
        line = line.strip()
        if len(line.split(":")) > 1 and len(line.split(":")[1]) > 0:
            numm = line.split(":")[0]
            numm = int(numm, 16)
            content = line.split(":")[1].split()[0]
            print("%08x %s" % ((numm, content)))