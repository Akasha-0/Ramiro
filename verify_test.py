from src.main import _get_effective_args
import argparse

p = argparse.ArgumentParser()
p.add_argument('-f', '--format', default=None)
args = p.parse_args([])
print(type(args).__name__)