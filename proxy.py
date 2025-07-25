import json
from fastapi import FastAPI, Request, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from jose import jwt, JWTError
from httpx import AsyncClient
from dotenv import load_dotenv
import asyncio


import os
import logging
import websockets



logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.StreamHandler()
    ]
)

load_dotenv()
JWT_PUBLIC_KEY = os.getenv("JWT_PUBLIC_KEY")
COMFYUI_URL = os.getenv("COMFYUI_URL")
ALGORITHM = os.getenv("ALGORITHM")
TARGET_WS_URL = os.getenv("TARGET_WS_URL")



app = FastAPI()
security = HTTPBearer()
http_client = AsyncClient(base_url=COMFYUI_URL)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 JWT Token"""
    if credentials is None:
        logging.error("Token 未提供")
        raise HTTPException(status_code=401, detail="Token 未提供")
    try:
        token = credentials.credentials
        logging.info(f"Received Token: {token}")
        token = token.strip()   
        token = token.replace("Bearer ", "").strip()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_token_json_path = os.path.join(script_dir, 'config_token.json')
        with open(config_token_json_path, "r") as f:
            config = json.load(f)
        if token in [item["token"] for item in config]:
            return True

        payload = jwt.decode(
            token,
            JWT_PUBLIC_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False,"verify_aud": False}
        )
        logging.info(f"Token 验证成功: {payload}")
        return payload
    except JWTError as e:
        logging.error(f"Token 验证失败: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Token 无效: {str(e)}")
    
async def conditional_verify_token(request: Request,credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """根据请求条件决定是否验证 Token"""
    logging.info(f"处理请求: {request.method} {request.url.path}")
    
    if request.method == "POST" and request.url.path == "/prompt":
        return await verify_token(credentials)
    
    if request.method == "POST" and request.url.path == "/api/prompt":
        return await verify_token(credentials)
    
    if request.method == "GET" and request.url.path == "/view":
        return
    
    return True
    # 限制访问
    raise HTTPException(status_code=401, detail=f"Token 无权限访问: {request.method} {request.url.path}")



@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str, _: dict = Depends(conditional_verify_token)):
    """代理请求至 ComfyUI"""
    logging.info(f"Forwarding {request.method} {path}")
    try:
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host", "origin", "referer"]}

        body = await request.body()

        response = await http_client.request(
            method=request.method,
            url=path,
            headers=headers,
            content=body,
            params=request.query_params
        )
        logging.info(f"Response status: {response.status_code}")
    
        return StreamingResponse(
            response.aiter_bytes(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )
    except ValueError:
        return response.content


@app.websocket("/ws")
async def websocket_proxy(websocket: WebSocket):
    """代理 WebSocket 请求至目标 WebSocket 服务"""
    await websocket.accept()
    target_ws = None
    client_closed = False
    tasks = []

    try:
        # 构造目标 WebSocket URL
        target_url = TARGET_WS_URL
        if websocket.query_params:
            params_str = "&".join([f"{key}={value}" for key, value in websocket.query_params.items()])
            target_url = f"{target_url}?{params_str}"
        
        logging.info(f"正在连接目标 WebSocket: {target_url}")

        # 连接目标 WebSocket
        target_ws = await websockets.connect(target_url)
        logging.info("目标 WebSocket 连接已建立")

        async def forward_to_target():
            """将客户端数据转发到目标 WebSocket"""
            nonlocal client_closed
            while not client_closed:
                try:
                    # 使用更高效的消息接收方式
                    message = await websocket.receive()
                    
                    # 减少日志量，只记录关键信息
                    if isinstance(message, (str, bytes)):
                        await target_ws.send(message)
                    else:
                        logging.warning(f"不支持的数据类型: {type(message)}")
                except WebSocketDisconnect:
                    logging.info("客户端 WebSocket 连接断开")
                    client_closed = True
                    break
                except asyncio.CancelledError:
                    logging.debug("转发到目标的任务被取消")
                    break
                except Exception as e:
                    logging.error(f"转发数据到目标时出错: {str(e)}", exc_info=True)
                    client_closed = True
                    break

        async def forward_to_client():
            """将目标 WebSocket 数据转发到客户端"""
            nonlocal client_closed
            while not client_closed:
                try:
                    message = await target_ws.recv()
                    
                    if isinstance(message, str):
                        await websocket.send_text(message)
                    elif isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    else:
                        logging.warning(f"不支持的数据类型: {type(message)}")
                except websockets.exceptions.ConnectionClosedOK:
                    logging.info("目标 WebSocket 连接正常关闭")
                    if not client_closed:
                        await websocket.close(code=1000, reason="目标连接已关闭")
                    client_closed = True
                    break
                except asyncio.CancelledError:
                    logging.debug("转发到客户端的任务被取消")
                    break
                except Exception as e:
                    logging.error(f"目标 WebSocket 出现异常: {str(e)}", exc_info=True)
                    if not client_closed:
                        await websocket.close(code=1011, reason=f"目标错误: {str(e)}")
                    client_closed = True
                    break

        # 创建任务
        tasks = [
            asyncio.create_task(forward_to_target(), name="client->target"),
            asyncio.create_task(forward_to_client(), name="target->client")
        ]

        # 等待任一任务完成
        done, pending = await asyncio.wait(
            tasks, 
            return_when=asyncio.FIRST_COMPLETED
        )

        # 取消未完成的任务
        for task in pending:
            task.cancel()
        
        # 等待被取消的任务完成
        await asyncio.gather(*pending, return_exceptions=True)

    except websockets.exceptions.WebSocketException as ws_err:
        logging.error(f"WebSocket连接错误: {str(ws_err)}", exc_info=True)
        if not client_closed:
            await websocket.close(code=1011, reason=f"连接错误: {str(ws_err)}")
    except Exception as e:
        logging.error(f"WebSocket 代理出错: {str(e)}", exc_info=True)
        if not client_closed:
            await websocket.close(code=1011, reason=f"内部错误: {str(e)}")
    finally:
        # 确保所有任务被取消
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # 确保目标 WebSocket 已关闭
        if target_ws:
            try:
                if not target_ws.closed:
                    await target_ws.close()
                    logging.debug("目标 WebSocket 连接已关闭")
            except Exception as e:
                logging.error(f"关闭目标连接时出错: {str(e)}")
        
        # 确保客户端 WebSocket 已关闭
        if not client_closed:
            try:
                # 使用更可靠的连接状态检查
                if not websocket.client_state == WebSocketState.DISCONNECTED:
                    await websocket.close()
                    logging.debug("客户端 WebSocket 连接已关闭")
            except Exception as e:
                logging.debug(f"关闭客户端连接时出错: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)