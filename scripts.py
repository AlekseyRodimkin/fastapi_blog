import subprocess

def lint():
    subprocess.run("black ./app/ && isort ./app/", shell=True, check=True)