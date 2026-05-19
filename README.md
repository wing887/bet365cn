# bet365cn

模拟 Bet365 中文版 — 移动端H5足球竞猜网站

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Pinia |
| 后端 | Python Flask + Gunicorn |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 反向代理 | Nginx |

## V1.0 玩法

- 胜平负（ML）
- 让球盘（Spread）
- 大小球（Totals）
- 波胆（Correct Score）

## 数据源

[odds-api.io](https://odds-api.io) — Bet365 + Sbobet

## 项目结构

```
bet365cn/
├── backend/          # Flask 后端
├── frontend/         # Vue 3 前端
├── nginx/            # Nginx 配置
├── scripts/          # 部署脚本
└── data/             # 球队名映射表
```

## 开发阶段

- [ ] Phase 1: 项目骨架 + 数据库模型
- [ ] Phase 2: 数据采集 + 定时任务
- [ ] Phase 3: 用户端 API
- [ ] Phase 4: 管理端 API
- [ ] Phase 5: 用户端前端
- [ ] Phase 6: 管理端前端
- [ ] Phase 7: Bet365 风格 UI
- [ ] Phase 8: 测试 + 部署
