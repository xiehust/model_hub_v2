## 如何启动前端

1. 前台启动
```bash
yarn install
yarn start
```


2. 使用PM2后台运行
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