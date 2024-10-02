import os
import subprocess
import time

p = subprocess.Popen(['i2cdetect', '-y','1'],stdout=subprocess.PIPE,) 
#cmdout = str(p.communicate())

for i in range(0,9):
   line = str(p.stdout.readline())
   print(line)