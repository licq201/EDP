# 安全扫描报告 - 2026-04-11 06:00

## 🔍 扫描概要

| 项目 | 状态 |
|------|------|
| 系统运行时间 | 1天3小时36分钟 |
| 内存使用 | 2.4GB / 3.8GB (63%) |
| 磁盘使用 | 16GB / 40GB (41%) |
| Gateway状态 | ⚠️ 需要检查 |

## ⚠️ 安全风险发现

### 高风险 🔴

1. **SSH Root登录启用**
   - `PermitRootLogin yes`
   - 建议: 改为 `PermitRootLogin no`

2. **SSH 密码认证启用**
   - `PasswordAuthentication yes`
   - 建议: 改为 `PasswordAuthentication no`，仅使用密钥

### 中风险 🟡

3. **缺少 Fail2Ban**
   - 未安装 fail2ban
   - SSH 暴力破解无防护
   - 建议: `apt install fail2ban`

4. **缺少自动安全更新**
   - unattended-upgrades 未配置
   - 系统安全更新需手动处理
   - 建议: `apt install unattended-upgrades`

### 低风险 🟢

5. **authorized_keys 需审查**
   - 存在2个密钥，其中 `your_email@example.com` 看起来像占位符
   - 建议: 确认是否需要，或删除

## 🔍 OpenClaw 安全审计

```
Summary: 0 critical · 1 warn · 1 info
```

| 项目 | 状态 | 说明 |
|------|------|------|
| gateway.trusted_proxies_missing | ⚠️ 警告 | 反向代理头未信任，如暴露控制面板需配置 |
| Attack Surface | ✅ 良好 | groups: open=0, allowlist=1 |
| tools.elevated | ℹ️ 信息 | 已启用 |
| browser control | ℹ️ 信息 | 已启用 |

## ✅ 安全配置（正常）

| 项目 | 状态 | 说明 |
|------|------|------|
| SSH密钥权限 | ✅ | .ssh 700, authorized_keys 600 |
| OpenSSH版本 | ✅ | 9.2p1 Debian (较新) |
| OpenSSL版本 | ✅ | 3.0.19 (较新) |
| Gateway绑定 | ✅ | 仅绑定 127.0.0.1，不对外暴露 |

## 📋 建议行动

**立即执行:**
```bash
# 1. 禁用 root SSH 登录
echo "PermitRootLogin no" >> /etc/ssh/sshd_config.d/hardening.conf
systemctl restart sshd

# 2. 禁用密码认证
echo "PasswordAuthentication no" >> /etc/ssh/sshd_config.d/hardening.conf
systemctl restart sshd

# 3. 安装 fail2ban
apt update && apt install fail2ban -y

# 4. 安装自动更新
apt install unattended-upgrades -y
dpkg-reconfigure unattended-upgrades
```

## 📅 下次扫描

下次安全扫描: 2026-04-12 06:00 (UTC+8)

---

**备注**: 昨天(04-10)发现的问题均未修复，需要人工介入处理。
