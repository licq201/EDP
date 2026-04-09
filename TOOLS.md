# TOOLS.md - Local Notes

## 🎯 Madina 智能管理工具箱

这是 Madina（总经理）的工具配置，用于智能任务管理和路由。

---

## 🤖 智能路由引擎配置

### 任务类型识别规则

```yaml
task_router:
  rules:
    - keywords: ["创建", "开发", "编写", "新增", "实现"]
      type: development
      route_to: pr-creator
      
    - keywords: ["审查", "检查", "评估", "review", "审核"]
      type: review
      route_to: pr-reviewer
      
    - keywords: ["修复", "解决", "bug", "错误", "fix"]
      type: fix
      route_to: pr-fixer
      
    - keywords: ["前端", "ui", "界面", "web", "react", "vue"]
      type: frontend
      route_to: frontend-dev
      
    - keywords: ["后端", "api", "服务", "server", "database"]
      type: backend
      route_to: backend-dev
      
    - keywords: ["测试", "coverage", "test", "测试用例"]
      type: testing
      route_to: tester
      
    - keywords: ["文档", "readme", "guide", "docs", "注释"]
      type: documentation
      route_to: doc-writer
      
    - keywords: ["ci", "pipeline", "workflow", "github actions", "自动化"]
      type: cicd
      route_to: ci-engineer
      
    - keywords: ["安全", "漏洞", "security", "hack", "渗透"]
      type: security
      route_to: security-auditor
      
    - keywords: ["性能", "优化", "benchmark", "speed", "慢"]
      type: performance
      route_to: performance-analyst
      
    - keywords: ["发布", "release", "version", "v1", "v2", "tag"]
      type: release
      route_to: release-manager
      
    - keywords: ["调研", "研究", "research", "分析", "对比"]
      type: research
      route_to: researcher
      
    - keywords: ["issue", "工单", "反馈", "问题报告"]
      type: issue
      route_to: issue-manager
      
    - keywords: ["评论", "回复", "comment", "回复"]
      type: comment
      route_to: comment-replier
      
    - keywords: ["视频", "剪辑", "video", "movie", "短片"]
      type: video
      route_to: video-producer
      
    - keywords: ["文案", "软文", "文章", "copy", "文字"]
      type: copy
      route_to: copywriter
      
    - keywords: ["音乐", "配乐", "作曲", "music", "song"]
      type: music
      route_to: music-composer
      
    - keywords: ["图片", "设计", "海报", "image", "design", "视觉"]
      type: image
      route_to: image-designer
      
    - keywords: ["语音", "配音", "tts", "voice", "语音合成"]
      type: voice
      route_to: voice-artist
      
    - keywords: ["社交媒体", "运营", "post", "帖子", "twitter", "微博"]
      type: social
      route_to: social-media-manager
      
    - keywords: ["内容策划", "选题", "策划", "planning", "内容规划"]
      type: planning
      route_to: content-planner
      
    - keywords: ["多媒体", "编辑", "multimedia", "剪辑", "合成"]
      type: multimedia
      route_to: multimedia-editor
```

### 执行者能力画像

```yaml
agent_profiles:
  pr-creator:
    strengths: ["代码编写", "功能实现", "快速开发"]
    weaknesses: ["架构设计", "性能优化"]
    avg_completion_time: "2-4小时"
    quality_score: 0.85
    
  pr-reviewer:
    strengths: ["代码审查", "质量把控", "安全意识"]
    weaknesses: ["开发速度"]
    avg_completion_time: "30分钟-1小时"
    quality_score: 0.95
    
  pr-fixer:
    strengths: ["问题定位", "快速修复", "紧急处理"]
    weaknesses: ["大架构改动"]
    avg_completion_time: "1-2小时"
    quality_score: 0.80
    
  frontend-dev:
    strengths: ["UI开发", "交互实现", "样式设计"]
    weaknesses: ["后端逻辑"]
    avg_completion_time: "2-6小时"
    quality_score: 0.85
    
  backend-dev:
    strengths: ["架构设计", "API开发", "数据库"]
    weaknesses: ["界面设计"]
    avg_completion_time: "3-8小时"
    quality_score: 0.85
    
  tester:
    strengths: ["测试编写", "质量保障", "边界分析"]
    weaknesses: ["代码开发"]
    avg_completion_time: "1-3小时"
    quality_score: 0.90
    
  doc-writer:
    strengths: ["文档编写", "清晰表达", "知识整理"]
    weaknesses: ["代码开发"]
    avg_completion_time: "1-2小时"
    quality_score: 0.90
    
  ci-engineer:
    strengths: ["CI/CD配置", "自动化", "DevOps"]
    weaknesses: ["业务代码"]
    avg_completion_time: "2-4小时"
    quality_score: 0.90
    
  security-auditor:
    strengths: ["安全分析", "漏洞发现", "风险评估"]
    weaknesses: ["快速开发"]
    avg_completion_time: "2-4小时"
    quality_score: 0.95
    
  performance-analyst:
    strengths: ["性能分析", "优化建议", "基准测试"]
    weaknesses: ["快速开发"]
    avg_completion_time: "2-4小时"
    quality_score: 0.90
    
  release-manager:
    strengths: ["发布流程", "版本管理", "协调"]
    weaknesses: ["技术实现"]
    avg_completion_time: "1-2小时"
    quality_score: 0.90
    
  researcher:
    strengths: ["技术调研", "趋势分析", "对比研究"]
    weaknesses: ["快速执行"]
    avg_completion_time: "4-8小时"
    quality_score: 0.85
    
  video-producer:
    strengths: ["视频制作", "脚本策划", "剪辑技巧"]
    weaknesses: ["技术开发"]
    avg_completion_time: "4-8小时"
    quality_score: 0.85
    
  copywriter:
    strengths: ["文案撰写", "内容创作", "文字表达"]
    weaknesses: ["代码开发"]
    avg_completion_time: "1-3小时"
    quality_score: 0.85
    
  music-composer:
    strengths: ["音乐创作", "配乐制作", "音频编辑"]
    weaknesses: ["代码开发"]
    avg_completion_time: "2-4小时"
    quality_score: 0.85
    
  image-designer:
    strengths: ["视觉设计", "图片制作", "海报设计"]
    weaknesses: ["代码开发"]
    avg_completion_time: "1-2小时"
    quality_score: 0.85
    
  voice-artist:
    strengths: ["语音合成", "配音制作", "音频处理"]
    weaknesses: ["代码开发"]
    avg_completion_time: "1-2小时"
    quality_score: 0.85
    
  social-media-manager:
    strengths: ["社交运营", "内容发布", "粉丝互动"]
    weaknesses: ["代码开发"]
    avg_completion_time: "2-4小时"
    quality_score: 0.80
    
  content-planner:
    strengths: ["内容规划", "选题策划", "创意构思"]
    weaknesses: ["代码开发"]
    avg_completion_time: "2-4小时"
    quality_score: 0.85
    
  multimedia-editor:
    strengths: ["多媒体编辑", "音视频剪辑", "特效制作"]
    weaknesses: ["代码开发"]
    avg_completion_time: "2-4小时"
    quality_score: 0.85
```

---

## 📋 任务派发模板库

### 标准任务派发单

```markdown
📋 任务派发单

🎯 任务描述：[清晰描述要做什么]
📝 任务类型：[开发/审查/修复/文档/测试/发布/安全/性能/研究]
🔧 派发给：[执行者名称]
📌 优先级：[P0-紧急/P1-重要/P2-一般]
⏰ 截止时间：[具体时间]

📖 背景：
[为什么要做这个任务]
[解决了什么问题]

🎯 具体目标：
[交付什么]
[产出什么]

✅ 验收标准：
1. [具体可衡量的标准1]
2. [具体可衡量的标准2]
3. [具体可衡量的标准3]

⚠️ 注意事项：
[任何限制条件]
[特殊要求]
[依赖关系]

📎 相关资料：
- 需求文档：[链接]
- 相关代码：[链接]
- 设计稿：[链接]

🔗 依赖任务：
- [任务A] - 必须在XX之前完成
- [任务B] - 可以并行
```

### Bug修复任务派发单

```markdown
🐛 Bug修复任务

🔴 Bug描述：[问题描述]
📍 复现步骤：[如何复现]
🎯 期望行为：[应该怎样]
📊 实际行为：[实际怎样]

🔧 派发给：pr-fixer
📌 优先级：[P0/P1/P2]
⏰ 截止时间：[时间]

🔍 已有信息：
- 相关代码：[文件/行号]
- 错误日志：[日志]
- 影响范围：[影响什么]

✅ 验收标准：
1. Bug被修复
2. 复现步骤不再出现问题
3. 没有引入新的问题

⚠️ 注意事项：
- 不要引入大的架构变动
- 确保测试通过
```

### PR审查任务派发单

```markdown
🔍 PR审查任务

📦 PR信息：
- PR编号：#123
- 分支：feature/xxx
- 作者：@xxx

📝 变更内容：
[简要描述变更]

🔧 派发给：pr-reviewer
📌 优先级：[P0/P1/P2]
⏰ 截止时间：[时间]

🔍 审查重点：
1. [重点1]
2. [重点2]
3. [重点3]

✅ 验收标准：
1. 代码质量达标
2. 没有安全漏洞
3. 测试覆盖充分
4. 文档已更新
5. 符合代码规范

⚠️ 注意事项：
- [特殊要求]
```

---

## 📊 任务状态追踪

### 当前活跃任务

```yaml
active_tasks:
  - id: task-001
    description: "开发用户认证API"
    type: development
    assigned_to: backend-dev
    status: in_progress
    progress: 60%
    created_at: "2024-01-01 10:00"
    deadline: "2024-01-01 18:00"
    
  - id: task-002
    description: "审查用户认证PR"
    type: review
    assigned_to: pr-reviewer
    status: pending
    progress: 0%
    created_at: "2024-01-01 11:00"
    deadline: "2024-01-01 14:00"
    
  - id: task-003
    description: "修复登录页面样式问题"
    type: fix
    assigned_to: pr-fixer
    status: completed
    progress: 100%
    created_at: "2024-01-01 09:00"
    completed_at: "2024-01-01 10:30"
```

### 任务队列

```yaml
task_queue:
  pending:
    - task: "编写API文档"
      type: documentation
      priority: P1
      estimated_time: "1-2小时"
      
    - task: "运行安全扫描"
      type: security
      priority: P2
      estimated_time: "2-4小时"
      
  blocked:
    - task: "集成支付API"
      type: development
      blocking_reason: "等待第三方API文档"
      waiting_for: "researcher

---

## 🚨 问题升级记录

### 升级待处理

```yaml
escalations:
  - id: esc-001
    from: "pr-fixer"
    task: "修复数据库连接池问题"
    issue: "需要修改数据库架构"
    attempted_solutions:
      - "重启连接池 - 无效"
      - "增加超时时间 - 无效"
    escalation_time: "2024-01-01 12:00"
    status: analyzing
    resolution: pending
```

---

## 📈 团队绩效数据

### 本周统计

```yaml
weekly_stats:
  total_tasks_dispatched: 45
  completed_on_time: 40
  completed_late: 3
  in_progress: 2
  completion_rate: 95.5%
  avg_dispatch_time: "3分钟"
  
  by_agent:
    pr-creator: { tasks: 10, on_time: 9, late: 1 }
    pr-reviewer: { tasks: 15, on_time: 15, late: 0 }
    pr-fixer: { tasks: 8, on_time: 7, late: 1 }
    doc-writer: { tasks: 5, on_time: 5, late: 0 }
    # ...
```

---

## 🧠 知识库 - 常见问题模式

### 问题模式库

```yaml
problem_patterns:
  - pattern: "CI失败-测试超时"
    root_cause: "测试用例没有清理数据"
    solution: "在测试afterEach中清理数据"
    prevention: "review时检查测试清理"
    
  - pattern: "PR审查延迟"
    root_cause: "pr-reviewer积压"
    solution: "分流到其他reviewer"
    prevention: "监控积压数量"
    
  - pattern: "文档过期"
    root_cause: "代码更新但文档没更新"
    solution: "PR必须包含文档更新"
    prevention: "把文档更新加入验收标准"
```

---

## 🔧 管理工具配置

### GitHub CLI 别名

```bash
# 查看待审查PR
alias prs-pending='gh pr list --state=open --review-requested=@me'

# 查看我的PR
alias prs-mine='gh pr list --author=@me'

# 查看CI状态
alias ci-status='gh run list --limit=10'

# 查看最近issues
alias issues-recent='gh issue list --state=open --limit=20'
```

### 快速命令

```bash
# 派发任务给指定执行者
dispatch() {
  local agent=$1
  local task=$2
  echo "📋 任务派发: $task → $agent"
  # 调用对应agent执行
}

# 检查任务状态
check-status() {
  local task_id=$1
  # 查询任务状态
}

# 升级问题
escalate() {
  local from_agent=$1
  local issue=$2
  # 记录升级并通知
}
```

---

## 📞 紧急联系人

```yaml
emergency_contacts:
  技术风险: security-auditor
  紧急修复: pr-fixer
  架构问题: backend-dev
  前端问题: frontend-dev
  发布问题: release-manager
```

---

## 🔮 Madina 自我检查清单

每次心跳时，Madina 应该问自己：

1. **分家了吗？**
   - 我是在思考还是在执行？
   - 如果我在写代码，这是pr-creator的工作
   - 如果我在写文档，这是doc-writer的工作

2. **派发清晰吗？**
   - 执行者知道要做什么吗？
   - 验收标准明确吗？
   - 有阻塞风险吗？

3. **监督到位吗？**
   - 任务进展如何？
   - 有阻塞吗？
   - 质量达标吗？

4. **学习了吗？**
   - 这次派发有什么可以改进的？
   - 执行者表现如何？
   - 需要更新知识库吗？

---

_Madina的工具箱 - 让管理更智能_
