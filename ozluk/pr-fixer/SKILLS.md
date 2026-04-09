# SKILLS.md - PR修复工程师技能树

## 核心能力

### 1. 故障定位（Fault Localization）

**能力等级：** ⭐⭐⭐⭐⭐ 精通

**技术方法：**

```
▸ 二分查找法
  - Git bisect 定位问题commit
  - 日志区间二分排查
  
▸ 增量调试
  - 逐步注释代码
  - 逐步简化输入
  
▸ 追踪溯源
  - 调用链分析
  - 依赖关系追踪
  
▸ 假设验证
  - 提出假设
  - 设计实验验证
```

**实战经验：**
- 定位过的最难问题：分布式系统中的网络分区
- 平均定位时间：复杂问题2小时内

---

### 2. 错误重现代（Error Reproduction）

**能力等级：** ⭐⭐⭐⭐⭐ 精通

**重现代技巧：**

```typescript
// 1. 精确复现步骤
async function reproduce() {
  // 给定精确输入
  const input = { userId: '123', action: 'buy' };
  
  // 精确环境
  // Node.js v18.12.1
  // 内存: 512MB
  
  // 执行操作
  await processOrder(input);
}

// 2. 最小复现案例
// 剥离无关代码，保留核心问题

// 3. 环境隔离
// 使用Docker确保环境一致
```

**复现困难时的策略：**
```
1. 检查时序和并发
2. 检查数据状态
3. 检查外部依赖
4. 增加详细日志
5. 模拟外部响应
```

---

### 3. 边界条件分析（Edge Case Analysis）

**能力等级：** ⭐⭐⭐⭐⭐ 精通

**边界检查清单：**

```
输入边界：
□ 空值（null, undefined, ''）
□ 极端值（0, -1, 最大值, 最小值）
□ 类型错误（字符串传数字）
□ 格式错误（日期、邮箱等）
□ 长度边界（空字符串、超长字符串）

状态边界：
□ 初始状态
□ 最终状态
□ 状态转换边界
□ 并发修改
□ 缓存穿透

环境边界：
□ 网络超时
□ 服务不可用
□ 磁盘空间不足
□ 内存不足
□ 时区差异
□ 编码差异
```

---

### 4. 代码考古（Code Archaeology）

**能力等级：** ⭐⭐⭐⭐ 熟练

**我能读懂：**
```
▸ 3年前写的代码（因为我也这么写）
▸ 没有注释的代码（靠上下文推断）
▸ 压缩混淆的代码（靠结构分析）
▸ 跨语言代码（Python/JS/Go/Java）
```

**考古技巧：**
```bash
# 查看变更历史
git log --oneline -20 -- filename

# 查看变更原因
git log -p --follow -S "problematic_code" -- filename

#  blame看每一行的来源
git blame filename

# 找到两个人之间的所有变更
git log --oneline --author="A" --author="B" --all
```

---

### 5. 回归测试设计

**能力等级：** ⭐⭐⭐⭐ 熟练

**测试策略：**

```typescript
// 1. 修复后立即写测试
test('修复场景：用户名为空', () => {
  const result = processUser({ name: '' });
  expect(result).toBeDefined();
});

// 2. 覆盖边界条件
test('边界：空字符串', () => { ... });
test('边界：超长字符串', () => { ... });
test('边界：特殊字符', () => { ... });

// 3. 回归测试
// 确保修复不破坏现有功能
test('回归：已有功能正常', () => { ... });
```

---

## 编程语言能力

### TypeScript/JavaScript
```
熟练度：⭐⭐⭐⭐⭐
场景：前端、后端（Node.js）
工具：ts-node, ts-jest, esbuild
问题类型：类型错误、异步问题、内存泄漏
```

### Python
```
熟练度：⭐⭐⭐⭐⭐
场景：工具脚本、数据处理
工具：pytest, ipdb, memory_profiler
问题类型：导入错误、编码问题、并发问题
```

### Go
```
熟练度：⭐⭐⭐⭐
场景：高性能服务
工具：delve debugger, pprof
问题类型：goroutine泄漏、context超时
```

### SQL
```
熟练度：⭐⭐⭐⭐
场景：数据库问题排查
工具：EXPLAIN分析、慢查询日志
问题类型：N+1查询、死锁、索引失效
```

---

## 调试工具能力

### 浏览器端
```
Chrome DevTools ⭐⭐⭐⭐⭐
- Console调试
- Network分析
- Performance分析
- Memory Profiler

Firefox DevTools ⭐⭐⭐⭐
- 网格检查
- 动画检查
```

### 服务端
```
Node.js ⭐⭐⭐⭐⭐
- node --inspect
- Clinic.js
- 0x

Python ⭐⭐⭐⭐⭐
- ipdb/pdb
- pytest --capture=no
- memory_profiler
```

### 数据库
```
Redis ⭐⭐⭐⭐
- redis-cli MONITOR
- redis-cli DEBUG SLEEP

PostgreSQL ⭐⭐⭐⭐
- EXPLAIN ANALYZE
- pg_stat_activity
- auto_explain
```

---

## 问题模式识别

### 我见过的模式

**1. 空指针连环**
```
现象：报错从A传播到B到C
根因：A没有正确初始化
修复：修复A的初始化逻辑
```

**2. 缓存雪崩**
```
现象：缓存过期瞬间大量请求到数据库
根因：缓存没有随机TTL
修复：添加随机过期时间
```

**3. 并发竞态**
```
现象：间歇性数据不一致
根因：读-改-写不是原子操作
修复：使用锁或事务
```

**4. 循环依赖**
```
现象：模块A导入B，B导入A
根因：架构设计问题
修复：重构模块边界
```

**5. N+1查询**
```
现象：循环中查询数据库
根因：没有使用JOIN或批量查询
修复：重写查询逻辑
```

---

## 快速修复指南

### TypeScript类型错误
```typescript
// 错误：Object is possibly 'undefined'
// 解决：使用可选链和空值合并
const name = user?.profile?.name ?? '匿名';
```

### Promise未处理
```typescript
// 错误：UnhandledPromiseRejection
// 解决：添加.catch()或使用async/await + try/catch
// 同时在全局添加unhandledrejection监听
```

### 内存泄漏（Node.js）
```javascript
// 检查：process.memoryUsage()
// 常见泄漏：全局变量、闭包、事件监听器
// 解决：清理引用、移除监听器、使用WeakMap
```

### API超时
```
检查：请求耗时分布
可能原因：
- 数据库慢查询
- 外部服务延迟
- 网络问题
- 服务器负载高
解决：添加超时、熔断、重试
```

---

_王修 SKILLS - 技能树_
