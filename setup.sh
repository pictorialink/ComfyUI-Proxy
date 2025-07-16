#!/bin/bash

# 定义环境变量内容 这个是启动的时候使用
ENV_CONTENT=$(cat <<EOF
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyUgYZ5sMtsJJsvePcy0u
BbksUQeQEdVUTk4675QY+7lNLc3Oj6DKOjpQbxS72IM5gm5N48AQh9OKidFvTnd6
N44X00xsNxHSxEB9f8lVkSyVBcJyIkkB+fmuHZK22OD7rHU5P4neAkEHUeq0TrjU
0N4JoiQCyMNLbXvVb0laC7CvIf/ZIud0BE5m/1+WSVpHqm9HvLLa1hxrwlMwSJOH
m2F9MaIRTe/EW31DA6tOHJ+niVw/pvvWQAxYi1zogd+LAcVCqGIaQv9hVqoyz/5k
97Xo5v5TmW72wJ/BgfD7Ui3XRnXIDD4cbxnFFcSEvgURR4CkH0qt6tNHACdUs/ts
mQIDAQAB
-----END PUBLIC KEY-----"
COMFYUI_URL="http://127.0.0.1:8188"
TARGET_WS_URL="ws://127.0.0.1:8188/ws"
ALGORITHM="RS256"
PORT=6006

EOF
)

# 创建 .env 文件并写入内容
echo "$ENV_CONTENT" > .env

# 检查 .env 文件是否创建成功
if [ -f ".env" ]; then
    echo ".env 文件已成功创建。"
else
    echo ".env 文件创建失败，请检查权限或路径。"
    exit 1
fi

# 安装依赖
pip install -r requirements.txt

# 启动代理服务
nohup python proxy.py > proxy.log 2>&1 &
