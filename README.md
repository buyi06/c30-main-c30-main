# C30管理面板 - 移动端Web管理界面

C30在线教育平台（iclass30）自动化系统的Web管理面板，支持状态可视化、手动操作、实时日志查看等功能。

## 技术栈

- **后端**: Python 3 + FastAPI
- **前端**: Vue 3 + Vant 4（移动端UI）+ Vite
- **调度**: APScheduler（内嵌FastAPI）
- **实时日志**: WebSocket
- **部署**: Docker + Nginx

## 快速开始

### Docker部署（推荐）

```bash
# 1. 编辑配置文件
cp config.json config.json.bak
# 修改config.json中的账号密码等配置

# 2. 构建并启动
docker-compose up -d --build

# 3. 访问管理面板
# 浏览器打开 http://your-server:8080
# 默认管理密码: admin123
```

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
# 前端开发服务器 http://localhost:5173，自动代理API到8000
```

## 功能

- **仪表盘**: 服务状态、今日课程、活动概览
- **课程详情**: 查看每个课程的活动列表和详情
- **手动操作**: 手动签到、讨论回复、头脑风暴提交、投票
- **实时日志**: WebSocket推送，按类型筛选
- **调度控制**: 暂停/恢复自动调度
- **配置管理**: 修改C30账号、自动回复内容、轮询间隔

## 目录结构

```
├── backend/          # FastAPI后端
│   ├── main.py       # 入口
│   ├── config.py     # 配置管理+JWT
│   ├── core/         # 核心层
│   │   ├── iclass30_api.py   # C30 API调用封装
│   │   ├── scheduler.py      # APScheduler调度
│   │   ├── state.py          # 全局状态
│   │   └── log_buffer.py     # 日志缓冲
│   └── api/          # API路由
│       ├── routes.py          # REST API
│       └── ws.py              # WebSocket
├── frontend/         # Vue 3前端
│   └── src/
│       ├── views/    # 页面
│       ├── components/ # 组件
│       ├── api/      # axios封装
│       └── utils/    # WebSocket客户端
├── config.json       # 运行时配置
├── Dockerfile        # 多阶段构建
├── docker-compose.yml
└── nginx.conf        # Nginx反代配置
```

## 配置说明

`config.json` 配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| admin_password | 管理面板登录密码 | admin123 |
| c30_username | C30平台用户名 | - |
| c30_password | C30平台密码 | - |
| auto_discuss_content | 讨论自动回复内容 | - |
| auto_brainstorm_content | 头脑风暴自动提交内容 | - |
| poll_intervals.pre_class | 课前轮询间隔(秒) | 60 |
| poll_intervals.in_class | 课中轮询间隔(秒) | 120 |
| poll_intervals.between | 课间轮询间隔(秒) | 1800 |
| poll_intervals.weekend | 周末轮询间隔(秒) | 7200 |
| log_max_lines | 日志最大行数 | 500 |

## API端点

### 认证
- `POST /api/auth/login` — 登录获取JWT

### 状态
- `GET /api/status` — 全局状态
- `GET /api/courses/today` — 今日课程
- `GET /api/courses/{id}/activities` — 课程活动
- `GET /api/activities/{id}/detail` — 活动详情

### 操作
- `POST /api/actions/sign/{id}` — 手动签到
- `POST /api/actions/discuss/{id}` — 手动讨论
- `POST /api/actions/brainstorm/{id}` — 手动头脑风暴
- `POST /api/actions/vote/{id}` — 手动投票
- `POST /api/actions/refresh` — 立即刷新

### 配置
- `GET /api/config` — 获取配置
- `PUT /api/config` — 修改配置
- `PUT /api/config/credentials` — 修改C30账号
- `PUT /api/config/password` — 修改管理密码

### 调度
- `POST /api/scheduler/pause` — 暂停
- `POST /api/scheduler/resume` — 恢复
- `GET /api/scheduler/jobs` — 任务列表

### WebSocket
- `WS /ws/logs` — 实时日志流