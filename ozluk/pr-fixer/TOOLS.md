# TOOLS.md - PR修复工程师工具箱

## 调试工具

### 版本控制
```bash
# Git bisect - 定位问题commit
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
git bisect run npm test

# Git log分析
git log --oneline --graph -20
git log -p -S "problematic_code" -- filename
git blame filename

# 变更比较
git diff HEAD~5..HEAD --stat
```

### 调试器
```bash
# Node.js
node --inspect index.js
# 然后Chrome://inspect

# Python
python -m pdb script.py
# 或
python -m ipdb script.py

# Go
dlv debug main.go
```

### 日志分析
```bash
# 实时日志
tail -f app.log

# 关键词搜索
grep -r "ERROR" logs/ | grep -v "timeout"

# 结构化日志解析
cat app.log | jq '. | select(.level == "error")'

# 按时间范围
sed -n '/2024-01-01 10:00/,/2024-01-01 11:00/p' app.log
```

---

## 性能分析

### CPU Profiling
```bash
# Node.js - 0x
npx 0x app.js

# Node.js - clinic
npx clinic doctor -- node app.js

# Python - cProfile
python -m cProfile -o output.prof app.py
python -m pstats output.prof
```

### 内存分析
```bash
# Node.js
node --inspect app.js
# Chrome DevTools > Memory > Heap Snapshot

# Python
python -m memory_profiler app.py
mprof run app.py
mprof plot output.dat
```

### 数据库
```sql
-- PostgreSQL EXPLAIN ANALYZE
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM users WHERE id = 1;

-- 慢查询日志
-- 在postgresql.conf中设置：
-- log_min_duration_statement = 1000
```

---

## API调试

### HTTP请求
```bash
# curl
curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}' \
  -v

# 带认证
curl -H "Authorization: Bearer $TOKEN" ...

# 请求耗时
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com/
```

### WebSocket调试
```javascript
// Chrome DevTools > Network > WS
// 可以查看WebSocket消息
```

---

## 数据库工具

### Redis
```bash
# 连接
redis-cli -h host -p port

# 监控操作
MONITOR

# 常用命令
KEYS pattern
GET key
HGETALL key
SCAN 0 MATCH pattern
```

### PostgreSQL
```bash
# 连接
psql -h host -U user -d database

# 查看连接
SELECT * FROM pg_stat_activity;

# 查看锁
SELECT * FROM pg_locks;

# 杀掉进程
SELECT pg_terminate_backend(pid);
```

---

## 容器环境

### Docker调试
```bash
# 进入容器
docker exec -it container_name /bin/bash

# 查看日志
docker logs -f container_name

# 查看资源使用
docker stats

# 检查网络
docker network inspect network_name
```

### Kubernetes
```bash
# Pod日志
kubectl logs -f pod-name

# 进入Pod
kubectl exec -it pod-name -- /bin/bash

# 查看Pod事件
kubectl describe pod pod-name

# 端口转发
kubectl port-forward pod-name 8080:80
```

---

## 监控和追踪

### 日志聚合
```bash
# ELK Stack
# Kibana中搜索
level:ERROR AND service:"user-service"

# Loki (Grafana)
{job="app"} |= "ERROR"
```

### 链路追踪
```bash
# Jaeger
# 查找trace
service:"api-gateway" operation:"/api/users"

# Zipkin
# 查找span
traceId="xxx" and spanName="/api/users"
```

### 指标监控
```bash
# Prometheus
# PromQL查询
rate(http_requests_total{status="500"}[5m])

# Grafana仪表板
# 常用面板：Error Rate, Latency, CPU, Memory
```

---

## 测试工具

### 单元测试
```bash
# Jest
npm test -- --coverage
npm test -- --watch
npm test -- -t "test name"

# Pytest
pytest -v
pytest -k "test_name"
pytest --cov=. --cov-report=html
```

### API测试
```bash
# Postman
# 导入collection运行测试

# curl测试
curl -s https://api.example.com/health | jq .
```

### 负载测试
```bash
# ab (Apache Bench)
ab -n 1000 -c 10 https://api.example.com/

# wrk
wrk -t12 -c100 -d30s https://api.example.com/
```

---

## 常用脚本

### 快速诊断脚本
```bash
#!/bin/bash
# 系统状态
echo "=== CPU & Memory ==="
top -bn1 | head -5
free -h

echo "=== Disk ==="
df -h

echo "=== Network ==="
netstat -i | head -10

echo "=== Process ==="
ps aux | grep -E "(node|python)" | head -10

echo "=== Docker ==="
docker ps -a | head -10
```

### 日志分析脚本
```bash
#!/bin/bash
# 统计错误类型
grep "ERROR" app.log | \
  sed 's/.*\(ERROR\|WARN\).*/\1/' | \
  sort | uniq -c | sort -rn
```

---

## 环境变量参考

```bash
# Node.js
NODE_ENV=development
NODE_OPTIONS="--inspect"
DEBUG=app:*

# Python
PYTHONPATH=.
LOG_LEVEL=DEBUG
ENV=development

# 数据库
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
```

---

## 配置参考

### IDE配置
```json
// VS Code - launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug",
      "program": "${workspaceFolder}/index.js",
      "runtimeArgs": ["--inspect"],
      "console": "integratedTerminal"
    }
  ]
}
```

### Git别名
```bash
# ~/.gitconfig
[alias]
  lg = log --oneline --graph --decorate -20
  st = status
  co = checkout
  br = branch
  last = log -1 HEAD
 visual = log --graph --oneline --decorate --all
```

---

_王修 TOOLS - 工欲善其事，必先利其器_
