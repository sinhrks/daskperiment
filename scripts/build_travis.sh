if [ "$TRAVIS_PYTHON_VERSION" == "2.7" ]; then
    wget -O conda.sh https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh
else
    wget -O conda.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
fi
bash conda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda

#Useful for debugging any issues with conda
conda info -a

conda create -n myenv "python=$PYTHON"
source activate myenv
conda install openblas
conda install numpy "pandas=$PANDAS" "dask=$DASK"

python -m pip install -r requirements.txt
python -m pip install -r requirements_test.txt
python -m pip install pytest pytest-cov codecov
python -m pip install flake8
