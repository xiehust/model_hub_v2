## ENV Setup

### Install python virtual env
```bash
conda create -n py311 python=3.11
conda activate py311
```

### Install requirements
```bash
pip install -r requirements.txt
```


### Run
```bash
python3 server.py --host 0.0.0.0 --port 8000 --api-keys 123456
```