# 国产大模型清单

从 [litellm](https://github.com/BerriAI/litellm) 模型库中自动筛选和标准化国产大模型信息。

## 功能特性

- 🕷️ **自动抓取**: 从 litellm 官方仓库获取最新模型数据
- 🎯 **智能筛选**: 自动识别国产模型（阿里云、百度、腾讯、智谱、月之暗面等）
- 📋 **标准化格式**: 统一的 JSON 格式输出
- 🔄 **自动化更新**: GitHub Actions 每天自动更新
- 🚀 **自动部署**: 通过 SSH/SCP 推送到阿里云 ECS

## 支持的国产模型提供商

| 提供商 | 模型示例 |
|--------|----------|
| 阿里云 | qwen, qwen-plus, qwen-turbo, qwen-max |
| 百度文心 | ernie-bot, wenxin |
| 零一万物 | yi-lightning, yi-large, yi-medium |
| 腾讯混元 | hunyuan, hunyuan-pro |
| 智谱AI | chatglm, glm-4, glm-4-air |
| 月之暗面 | moonshot, kimi |
| 深度求索 | deepseek-chat, deepseek-coder |
| 讯飞星火 | spark, xinghua |
| 火山引擎 | doubao, volcengine |

## 本地使用

```bash
# 安装依赖
pip install -r requirements.txt

# 运行脚本
python fetch_domestic_models.py

# 输出文件: output/domestic_llm_models.json
```

## GitHub Actions 配置

### 1. 设置 Secrets

在 GitHub 仓库设置中添加以下 Secrets：

| Secret 名称 | 说明 | 示例 |
|-------------|------|------|
| `ECS_HOST` | ECS 服务器 IP 或域名 | `1.2.3.4` 或 `your-server.com` |
| `ECS_PORT` | SSH 端口（可选） | `22` |
| `ECS_USER` | SSH 登录用户名 | `root` |
| `ECS_PATH` | 服务器目标路径（可选） | `/api_data/llm` |
| `ECS_SSH_KEY` | SSH 私钥 | PEM 格式私钥内容 |

### 2. SSH 密钥生成

```bash
# 生成 SSH 密钥对
ssh-keygen -t ed25519 -f ~/.ssh/ecs_deploy -C "github-actions"

# 将公钥添加到 ECS
ssh-copy-id -i ~/.ssh/ecs_deploy.pub user@your-ecs-host

# 或者手动添加公钥到服务器的 ~/.ssh/authorized_keys
cat ~/.ssh/ecs_deploy.pub
```

将私钥内容添加到 GitHub Secrets `ECS_SSH_KEY`：
```bash
cat ~/.ssh/ecs_deploy
```

### 3. 服务器配置

确保服务器上的 SSH 用户有权限访问目标目录：

```bash
# 创建目标目录
mkdir -p /api_data/llm

# 设置权限
chmod 755 /api_data/llm
```

## 输出格式

```json
{
  "metadata": {
    "version": "1.0.0",
    "last_updated": "2026-03-13T12:00:00.000000",
    "total_models": 150,
    "source": "https://github.com/BerriAI/litellm",
    "description": "国产大模型清单 - 从 litellm 筛选并标准化"
  },
  "models": {
    "qwen-plus": {
      "mode": "chat",
      "litellm_provider": "deepseek",
      "max_tokens": 128000,
      "max_input_tokens": 128000,
      "max_output_tokens": 8192,
      "input_cost_per_token": 0.00001,
      "output_cost_per_token": 0.00002,
      "supports_function_calling": true,
      "supports_vision": true,
      "supports_system_messages": true
    }
  }
}
```

## 定时任务

- **自动更新**: 每天 UTC 02:00 (北京时间 10:00)
- **手动触发**: 在 Actions 页面手动运行

## 故障排除

### SSH 连接失败

检查 ECS 安全组是否开放 22 端口，允许 GitHub Actions IP 访问。

### 权限被拒绝

确保：
1. SSH 公钥已正确添加到服务器的 `~/.ssh/authorized_keys`
2. 目标目录存在且有写入权限
3. SSH 用户有访问该目录的权限

### 未配置 ECS 同步

如果未配置 ECS 相关的 Secrets，workflow 会自动跳过部署步骤，不会报错。配置后会自动启用。
