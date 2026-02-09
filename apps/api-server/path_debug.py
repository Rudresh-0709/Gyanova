import os
import sys

print(f"__file__: {__file__}")
print(f"abspath: {os.path.abspath(__file__)}")
print(f"dirname: {os.path.dirname(os.path.abspath(__file__))}")
print(f"cwd: {os.getcwd()}")
