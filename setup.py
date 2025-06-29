#!/usr/bin/env python3
"""
This creates a virtual environment in the working directory defined in config.yaml.
It then installs my branch of PyCS3, and optionally runs `initial_guess.ipynb` to 
produce pickled light curves ready to be used by the subsequent scripts.
"""
import os
import sys
import subprocess
import yaml
import venv
import shutil

from utils.config import read_config


def check_python_version():
    """
    ensures the python version is 3.8 or higher.
    """
    if sys.version_info < (3, 8):
        sys.exit("python >=3.8 most likely best, you have ", sys.version_info)

def create_virtualenv(workdir, env_name='td_release_env'):
    """
    create a virtual environment in $workdir.
    """
    env_path = os.path.join(workdir, env_name)
    if os.path.exists(env_path):
        print(f"Virtual environment already exists at {env_path}")
    else:
        print(f"Creating virtual environment at {env_path}")
        venv.create(env_path, with_pip=True)
    return env_path

def run_command(command, env=None, cwd=None):
    """
    run a system command, handle errors.
    """
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, env=env, cwd=cwd)
    if result.returncode != 0:
        sys.exit(f"Command {' '.join(command)} failed with exit code {result.returncode}")

def install_dependencies(env_path, dependencies):
    """
    install the required Python dependencies.
    """
    pip_executable = get_pip_executable(env_path)
    print("Upgrading pip...")
    run_command([pip_executable, 'install', '--upgrade', 'pip'])
    print("Installing dependencies...")
    run_command([pip_executable, 'install'] + dependencies)

def get_pip_executable(env_path):
    """
    return the path to the pip executable in the virtual environment.
    """
    if os.name == 'nt':
        # sure hope not ...
        return os.path.join(env_path, 'Scripts', 'pip.exe')
    else:
        return os.path.join(env_path, 'bin', 'pip')

def clone_pycs3(workdir, repo_url='https://gitlab.com/cosmograil/PyCS3.git', branch='fred_td_release'):
    """
    clone the PyCS3 repository, check out my branch
    """
    repo_dir = os.path.join(workdir, 'PyCS3')
    if os.path.exists(repo_dir):
        print(f"PyCS3 repository already exists at {repo_dir}")
    else:
        print(f"Cloning PyCS3 from {repo_url} into {repo_dir}")
        run_command(['git', 'clone', repo_url, repo_dir])
    # Checkout the specified branch
    run_command(['git', 'checkout', branch], cwd=repo_dir)
    return repo_dir

def install_pycs3(repo_dir, env_path):
    """
    pip -e the clone
    """
    pip_executable = get_pip_executable(env_path)
    print("Installing PyCS3 in editable mode...")
    run_command([pip_executable, 'install', '-e', repo_dir])

def run_notebook(env_path, notebook_path):
    """
    run a jupyter notebook headlessly.
    """
    jupyter_executable = get_jupyter_executable(env_path)
    if not os.path.exists(jupyter_executable):
        print("Jupyter executable not found. Installing Jupyter...")
        pip_executable = get_pip_executable(env_path)
        run_command([pip_executable, 'install', 'jupyter'])
    print(f"Running notebook {notebook_path} headlessly...")
    run_command([
        jupyter_executable, 'nbconvert',
        '--to', 'notebook',
        '--execute',
        '--inplace',
        notebook_path
    ])

def get_jupyter_executable(env_path):
    """
    Returns the path to the Jupyter executable in the virtual environment.
    """
    if os.name == 'nt':
        # :(
        return os.path.join(env_path, 'Scripts', 'jupyter.exe')
    else:
        return os.path.join(env_path, 'bin', 'jupyter')

def main():
    # 1: check python version
    check_python_version()
    
    # 2: read configuration
    config = read_config('config.yaml')
    workdir = config.get('workdir')
    if not workdir:
        sys.exit("The 'workdir' key is not defined in config.yaml.")
    if not os.path.isabs(workdir):
        # make workdir absolute relative to the config file
        workdir = os.path.abspath(workdir)
    os.makedirs(workdir, exist_ok=True)
    
    # 3: create virtual environment
    env_path = create_virtualenv(workdir)
    
    # 4: install dependencies
    dependencies = ['numpy<2.0', 'matplotlib', 'scipy', 'scikit-learn', 
                    'multiprocess', 'jupyter', 'pandas', 'cdspyreadme']
    install_dependencies(env_path, dependencies)
    
    # 5: clone and set up PyCS3
    pycs3_dir = clone_pycs3(workdir)
    install_pycs3(pycs3_dir, env_path)
    
    # 6: offer to run the initial guess notebook, mainly to create pickled light curves that
    # I do not want to include in the git repo
    message = """\n\n\n\n`initial_guess.ipynb` contains my chosen params for td estimation. 
It also creates pickled light curves (not included in the repo) ready to be used by the subsequent PyCS3 scripts.
Do you want to run 'initial_guess.ipynb' headlessly? (y/n): """
    choice = input(message).strip().lower()
    if choice == 'y':
        notebook_path = os.path.join(os.getcwd(), 'initial_guess.ipynb')
        if not os.path.exists(notebook_path):
            print(f"Notebook {notebook_path} does not exist.")
        else:
            run_notebook(env_path, notebook_path)
    else:
        print("Skipping notebook execution.")
    

if __name__ == '__main__':
    main()

