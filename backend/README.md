# 后端环境安装

## 1.安装 python virtual env
- 进入backend目录
```bash
cd backend
```
- 安装miniconda
```bash
wget  https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x  Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh  -b -f -p ../miniconda3
source  ../miniconda3/bin/activate
conda create -n py311 python=3.11
conda activate py311
```

## 2.安装 requirements
```bash
pip install -r requirements.txt
```

## 3.配置MYSQL
- 安装Docker
 **Note: Execute each command one line at a time.**
```bash  
# Install components
sudo apt-get update
sudo apt install docker python3-pip git -y && pip3 install -U awscli && pip install pyyaml==5.3.1

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io
# Configure components
sudo systemctl enable docker && sudo systemctl start docker && sudo usermod -aG docker $USER

```
- **你需要注销并重新登录才能使上面更改生效。**

- 在backend目录下执行以下命令启动mysql容器
```bash
docker run -d \
  --name hub-mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=1234560 \
  -e MYSQL_DATABASE=llm \
  -e MYSQL_USER=llmdata \
  -e MYSQL_PASSWORD=llmdata \
  -v mysql-data:/var/lib/mysql \
  -v $(pwd)/scripts:/opt/data \
  --restart always \
  mysql:8.0
```

- 等待1-2分钟之后，验证是否成功:
```bash
docker ps
```

- 进入backend/scripts目录，执行以下命令创建数据库:
```bash
cd scripts 

docker exec hub-mysql sh -c "mysql -u root -p1234560 -D llm  < /opt/data/mysql_setup.sql"
```

### 其他命令（仅供参考，不用执行）
- To login in cmd line
```bash
docker exec -it hub-mysql mysql -u root -p1234560
```

- To stop the container when you're done, use:
```bash
docker stop hub-mysql
```

- To remove the container when you're done, use:
```bash
docker rm hub-mysql
```

- To start it again later, use:
```bash
docker start hub-mysql
```

## 3.添加用户
```bash
python3 users/add_user.py
```
请自行添加用户民和密码，并保存到安全的位置。


## 4.后台启动进程
1. 进入backend目录下启动web server进程  
```bash
cd backend
pm2 start server.py --name "modelhub-server" --interpreter python3 -- --host 0.0.0.0 --port 8000
```
2. 启动任务处理引擎
- 可选，前台启动sever进程
```bash
pm2 start processing_engine/main.py --name "modelhub-engine" --interpreter python3
```



## 5.安装nginx（可选）
- 安装nginx
```bash
sudo apt update 
sudo apt install nginx
```

- 创建nginx配置文件  
目的：
  让后端webserver Listens on port 443 without SSL  
  Forwards requests to your application running on localhost:8000  

注意需要把xxx.compute.amazonaws.com改成实际的ec2 dns名称
```bash 
sudo vim /etc/nginx/sites-available/modelhub
```

```nginx
server {
    listen 80;
    server_name xxx.compute.amazonaws.com;
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443;
    server_name xxx.compute.amazonaws.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

- 更改server name bucket size 
- 打开nginx配置文件
```bash
sudo vim /etc/nginx/nginx.conf
```
- 把server_names_hash_bucket_size 改成256
```nginx
http {
    server_names_hash_bucket_size 256;
    # ... other configurations ...
}
```

- 生效配置:
```bash
sudo ln -s /etc/nginx/sites-available/modelhub /etc/nginx/sites-enabled/ 
sudo nginx -t 
sudo systemctl restart nginx
```