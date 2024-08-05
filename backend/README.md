# 后端环境安装

## 1.安装 python virtual env
1. 进入backend目录下执行以下命令 
```bash
cd backend
bash 01.setup.sh
```

## 2.添加用户
```bash
python3 users/add_user.py
```
请自行添加用户民和密码，并保存到安全的位置。


## 3.后台启动进程
1. 进入backend目录下启动web server进程  
```bash
pm2 start server.py --name "modelhub-server" --interpreter python3 -- --host 0.0.0.0 --port 8000
```
2. 启动任务处理引擎
- 可选，前台启动sever进程
```bash
pm2 start processing_engine/main.py --name "modelhub-engine" --interpreter python3
```


## 4.安装nginx（可选）
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