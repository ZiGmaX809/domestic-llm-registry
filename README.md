# 国产大模型清单

从 [litellm](https://github.com/BerriAI/litellm) 模型库中自动筛选和标准化国产大模型信息。

## 功能特性

- 🕷️ **自动抓取**: 从 litellm 官方仓库获取最新模型数据
- 🎯 **智能筛选**: 自动识别国产模型（阿里云、百度、腾讯、智谱、月之暗面等）
- 📋 **标准化格式**: 统一的 JSON 格式输出
- 🔄 **自动化更新**: GitHub Actions 每天自动更新
- 🚀 **自动部署**: 推送到阿里云 ECS

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
| `ECS_USER` | SSH 登录用户名 | `root` |
| `ECS_PATH` | 服务器目标路径 | `/data/domestic-llm-registry` |
| `ECS_SSH_KEY` | SSH 私钥 | PEM 格式私钥内容 |

### 2. SSH 密钥生成

```bash
# 生成 SSH 密钥对
ssh-keygen -t ed25519 -f ~/.ssh/ecs_deploy -C "github-actions"

# 将公钥添加到 ECS
ssh-copy-id -i ~/.ssh/ecs_deploy.pub user@your-ecs-host

# 将私钥内容添加到 GitHub Secrets
cat ~/.ssh/ecs_deploy
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

### SFTP 上传失败：No such file or directory

**原因**: SFTP 用户可能被 chroot 限制，无法访问完整系统路径。

**解决方案**:

1. **查看 SFTP 根目录**: Workflow 会自动显示 `pwd` 输出，确认 SFTP 用户的根目录

2. **使用相对路径**: 如果 SFTP 根目录是 `/home/username`，目标路径设为 `api_data/llm` 而非 `/var/www/...`

3. **修改 ECS 路径设置**:
   - 修改 GitHub Secrets 中的 `ECS_PATH`
   - 使用 SFTP 根目录下的相对路径

4. **手动创建目录** (如果 SFTP 服务器支持):
   ```bash
   # 在服务器上创建目标目录
   mkdir -p /var/www/casecat.cn/api_data/llm
   chmod 755 /var/www/casecat.cn/api_data/llm
   ```

### SFTP 连接超时

检查 ECS 安全组是否开放 22 端口，允许 GitHub Actions IP 访问。
