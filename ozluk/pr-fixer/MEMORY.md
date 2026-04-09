# MEMORY.md - PR修复工程师经验库

## 经验教训

### 🔴 教训1：没有测试的修复是危险的修复

**事件：**
修复了一个空指针问题，本地测试通过。发布后用户反馈更多问题。

**根因：**
修复引入了边界条件改变，但没有更新测试。

**学到的：**
```
修复前：先看有没有测试
修复后：更新或新增测试
发布前：确保测试覆盖修复的场景
```

---

### 🔴 教训2：别在压力下妥协

**事件：**
业务催促，快速修复了一个bug。第二天同样的bug在另一个地方出现。

**根因：**
只修复了症状，没有分析根因。

**学到的：**
```
宁可多花1小时理解，不要少花5分钟修错。
```

---

### 🔴 教训3：生产问题不要猜测

**事件：**
根据日志猜测问题原因，结果猜错了，差点引入新bug。

**根因：**
没有足够信息就下结论。

**学到的：**
```
猜测是可以的，但猜测后要验证。
用实验证明猜测，而不是相信猜测。
```

---

### 🟡 教训4：有时候回滚比修复快

**事件：**
修复了一个复杂问题，花了4小时。回滚只需要5分钟。

**根因：**
问题紧急，但修复方案复杂。

**学到的：**
```
紧急情况下：
1. 先止血（回滚/降级）
2. 再修复
3. 最后验证
```

---

### 🟡 教训5：跨时区问题很难调

**事件：**
用户在南半球，时间显示错误。

**根因：**
代码用了本地时区而不是UTC。

**学到的：**
```
时间处理：
- 存储：UTC
- 显示：本地时区
- 传输：ISO8601格式
```

---

## 常见问题模式库

### 1. 空指针传播链

**症状：** 报错信息指向NPE，但真正问题在初始化

**定位技巧：**
```
1. 看NPE在哪一行
2. 分析为什么对象为空
3. 追踪对象创建链
4. 检查是否有异步问题
```

**预防：**
```typescript
// 使用非空断言前先检查
if (user?.profile?.address) {
  const city = user.profile.address.city;
}
```

---

### 2. 缓存雪崩

**症状：** 缓存同时过期，请求打到数据库

**定位技巧：**
```
1. 看数据库慢查询时间点
2. 检查缓存TTL配置
3. 分析是否大量key同时过期
```

**预防：**
```typescript
// 不要所有key设相同TTL
const ttl = baseTtl + random jitter(0, baseTtl * 0.1);
```

---

### 3. 并发写冲突

**症状：** 数据不一致，丢数据

**定位技巧：**
```
1. 检查是否有无锁并发写
2. 看事务隔离级别
3. 分析操作是否有先后依赖
```

**预防：**
```sql
-- 使用乐观锁
SELECT version FROM users WHERE id = 1;
UPDATE users SET name = 'new', version = version + 1 
WHERE id = 1 AND version = 1;
```

---

### 4. N+1查询

**症状：** 查询不快，数据量大了就慢

**定位技巧：**
```
1. 看日志中数据库查询数量
2. EXPLAIN分析查询计划
3. 检查是否在循环中查询
```

**预防：**
```typescript
// 批量查询代替循环查询
const userIds = orders.map(o => o.userId);
const users = await User.findAll({ where: { id: userIds } });
```

---

### 5. 异步地狱

**症状：** 代码执行顺序不对，结果不对

**定位技巧：**
```
1. 检查async/await使用
2. 看Promise.all使用是否正确
3. 分析回调顺序
```

**预防：**
```typescript
// 好：清晰顺序
const a = await fetchA();
const b = await fetchB(a);

// 好：可并行
const [a, b] = await Promise.all([fetchA(), fetchB()]);

// 差：嵌套回调
fetchA().then(a => {
  fetchB(a).then(b => {
    fetchC(b).then(c => console.log(c));
  });
});
```

---

## 修复检查清单

### 修复前必查
```
□ 理解问题本质了吗？
□ 能复现吗？
□ 影响范围清楚吗？
□ 有没有类似问题？
```

### 修复中必查
```
□ 最小改动原则
□ 防御性编程
□ 边界情况
□ 错误处理
```

### 修复后必查
```
□ 测试通过了吗？
□ CI通过了吗？
□ 覆盖修复场景了吗？
□ 影响功能正常吗？
□ 文档更新了吗？
```

---

## 问题知识库

### 问题：数据库连接池耗尽

**症状：**
```
Error: Cannot create a new connection to the database
Connection pool exhausted
```

**排查：**
```sql
-- 检查活跃连接
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- 检查等待连接
SELECT * FROM pg_stat_activity WHERE waiting = true;

-- 最大连接数
SHOW max_connections;
```

**原因：**
- 连接泄漏（没关闭）
- 连接没复用
- 查询太慢占用连接
- 连接池配置太小

**解决方案：**
```typescript
// 1. 确保连接关闭
try {
  const result = await query();
} finally {
  await connection.release(); // 或 close()
}

// 2. 增大连接池
const pool = new Pool({ max: 50 });

// 3. 查询超时
await query({ timeout: 5000 });
```

---

### 问题：内存泄漏

**症状：**
```
Process PID: 12345
Memory: 2GB → 3GB → 4GB → OOM
```

**排查：**
```javascript
// Node.js
console.log(process.memoryUsage());
// { rss: 2GB, heapTotal: 1GB, heapUsed: 800MB }

// 多次快照对比
// Chrome DevTools > Memory > Heap Snapshot
```

**常见原因：**
- 全局变量累积
- 闭包引用
- 事件监听器没移除
- 缓存没限制大小

**解决方案：**
```typescript
// 1. 清理事件监听器
emitter.off('event', handler);

// 2. 限制缓存大小
const cache = new LRUCache({ max: 1000 });

// 3. 使用WeakMap
const cache = new WeakMap();
```

---

### 问题：进程僵死

**症状：**
```
进程存在但不响应
CPU 0%
日志停止输出
```

**排查：**
```bash
# 检查进程状态
ps aux | grep node

# 看系统调用
strace -p PID

# 看打开的文件
lsof -p PID
```

**常见原因：**
- 死锁
- 同步阻塞在等待
- 外部服务超时

**解决方案：**
```typescript
// 1. 添加超时
const result = await promise.race([
  doSomething(),
  new Promise((_, reject) => 
    setTimeout(() => reject(new Error('Timeout')), 5000)
  )
]);

// 2. 使用AbortController
const controller = new AbortController();
setTimeout(() => controller.abort(), 5000);
await fetch(url, { signal: controller.signal });
```

---

## 修复案例库

### 案例1：支付回调重复处理

**问题：** 同一个支付回调被处理了两次，导致重复发货

**分析：**
```typescript
// 原代码
async function handlePaymentCallback(orderId: string) {
  const order = await Order.findById(orderId);
  if (order.status === 'paid') return; // 检查
  
  await processPayment(order);
  await order.update({ status: 'paid' });
}

// 问题：并发请求通过检查
// 原因：检查和更新不是原子操作
```

**修复：**
```typescript
// 方案1：使用事务
await db.transaction(async (trx) => {
  const order = await Order.query(trx)
    .where('id', orderId)
    .where('status', '!=', 'paid')
    .first();
  
  if (!order) return; // 已经被处理
  
  await processPayment(order);
  await order.query(trx).patch({ status: 'paid' });
});

// 方案2：分布式锁
const lock = await redis.lock(`payment:${orderId}`, 3000);
try {
  // 处理逻辑
} finally {
  await lock.release();
}
```

---

### 案例2：导出Excel内存溢出

**问题：** 导出大数据量Excel时进程OOM

**分析：**
```typescript
// 原代码
async function exportOrders() {
  const orders = await Order.findAll(); // 全部加载到内存
  const excel = new Excel();
  
  for (const order of orders) {
    excel.addRow(order); // 每行都创建对象
  }
  
  return excel.toBuffer();
}

// 问题：10万条数据全部在内存
```

**修复：**
```typescript
// 使用流式处理
async function exportOrders() {
  const stream = new PassThrough();
  const excel = new Excel({ stream });
  
  // 流式写入
  Order.findAll({ batchSize: 1000 })
    .forEach(batch => {
      for (const order of batch) {
        excel.addRow(order);
      }
    })
    .then(() => excel.end())
    .catch(err => excel.destroy(err));
  
  return stream;
}
```

---

_王修 MEMORY - 经验是最好的老师_
