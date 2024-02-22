import pytest
import sys
import subprocess

def test_single_write(filename="file1"):
    data = "somerandomdatasomerandomdatasomerandomdatasomerandomdata"
    result = subprocess.run(["python", "xinucli/xinucli.py", "write", filename, data], capture_output=True, text=True)
    assert result.returncode == 0

def test_100_writes():
    for i in range(0, 100):
        f = f'file{i}'
        test_single_write(filename=f)

def test_single_read(filename="file1"):
    data = "somerandomdatasomerandomdatasomerandomdatasomerandomdata"
    result = subprocess.run(["python", "xinucli/xinucli.py", "read", filename], capture_output=True, text=True)
    assert result.returncode == 0
    assert data in result.stdout

def test_100_reads():
    for i in range(0, 100):
        f = f'file{i}'
        test_single_read(filename=f)

def test_del():
    for i in range(0, 100):
        f = f'file{i}'
        result = subprocess.run(["python", "xinucli/xinucli.py", "rm", f], capture_output=True, text=True)
        assert result.returncode == 0

