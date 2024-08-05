## 环境安装
- 硬件需求：一台ec2 Instance, m5.xlarge, 200GB EBS storage
- os需求：ubuntu 22.04
- 配置权限：
- 在IAM中创建一个role，select trust type: AWS service, service: EC2, policy: AmazonSageMakerFullAccess
- ![alt text](./assets/image_iamrole.png)
- ![alt text](./assets/image_iamrole2.png)
- ![alt text](./assets/image_iamrole3.png)

- 把ec2 instance attach到role
- ![alt text](./assets/image.png)


## 启动前端
1. 安装nodejs 18
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install --global yarn
```
2. 配置环境变量
- 修改model_hub_v2/env.sample 文件中,ip改成对应的ec2的ip，随机给一个api key，这个key需要与下一部分后端配置backend/.env中的apikey保持一致
```
REACT_APP_API_ENDPOINT=http://{ip}:8000/v1
REACT_APP_API_KEY=随机给一个key
```



3. 启动web
- 安装yarn
```bash
yarn install
```

```bash
#install pm2
sudo yarn global add pm2
pm2 start pm2run.config.js 
```
- 以下是其他的管理命令:
```bash
pm2 list
pm2 stop modelhub
pm2 restart modelhub
pm2 delete modelhub
```

## 后端配置
请见[后端配置](./backend/README.md)