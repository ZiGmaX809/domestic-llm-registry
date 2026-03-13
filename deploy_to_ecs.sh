#!/bin/bash
#
# 国产模型清单 - ECS 部署脚本
# 使用 SSH + SCP 方式上传文件到阿里云 ECS
# 参考 LPR 项目的部署方式
#

set -e

# ==================== 配置区域 ====================
# 从环境变量读取
ECS_HOST="${ECS_HOST:-your-server.com}"
ECS_PORT="${ECS_PORT:-22}"
ECS_USER="${ECS_USER:-github_sync}"
ECS_PATH="${ECS_PATH:-/api_data/llm}"
ECS_SSH_KEY="${ECS_SSH_KEY:-}"

# 本地文件路径
LOCAL_FILE="output/domestic_llm_models.json"
# ================================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

# 检查配置
check_config() {
    if [ -z "$ECS_HOST" ] || [ "$ECS_HOST" = "your-server.com" ]; then
        log_error "ECS_HOST 未配置"
        echo "请设置环境变量: export ECS_HOST=your-server.com"
        exit 1
    fi

    if [ -z "$ECS_SSH_KEY" ]; then
        log_error "ECS_SSH_KEY 未配置"
        echo "请设置环境变量: export ECS_SSH_KEY=\"\$(cat ~/.ssh/your_key)\""
        exit 1
    fi

    if [ ! -f "$LOCAL_FILE" ]; then
        log_error "本地文件不存在: $LOCAL_FILE"
        echo "请先运行: python fetch_domestic_models.py"
        exit 1
    fi
}

# 显示配置
show_config() {
    echo ""
    echo "=========================================="
    echo "🚀 开始部署到阿里云 ECS"
    echo "=========================================="
    echo "🖥️  服务器: $ECS_USER@$ECS_HOST:$ECS_PORT"
    echo "📂 目标路径: $ECS_PATH"
    echo "📄 本地文件: $LOCAL_FILE"
    echo "=========================================="
    echo ""
}

# 设置 SSH 密钥
setup_ssh_key() {
    log_step "配置 SSH 密钥..."
    mkdir -p ~/.ssh
    echo "$ECS_SSH_KEY" > ~/.ssh/id_rsa_deploy
    chmod 600 ~/.ssh/id_rsa_deploy

    # 添加到 known_hosts
    ssh-keyscan -p $ECS_PORT -H $ECS_HOST >> ~/.ssh/known_hosts 2>/dev/null || true
}

# 测试 SSH 连接
test_connection() {
    log_step "测试 SSH 连接..."

    if ssh -o StrictHostKeyChecking=no \
            -o IdentityFile=~/.ssh/id_rsa_deploy \
            -o Port=$ECS_PORT \
            -o BatchMode=yes \
            -o ConnectTimeout=10 \
            $ECS_USER@$ECS_HOST "echo 'Connection OK'" > /dev/null 2>&1; then
        log_info "SSH 连接成功"
    else
        log_error "SSH 连接失败"
        echo ""
        echo "请检查："
        echo "1. ECS_HOST 是否正确"
        echo "2. ECS_USER 是否正确"
        echo "3. ECS_SSH_KEY 是否正确"
        echo "4. 服务器防火墙是否开放 $ECS_PORT 端口"
        exit 1
    fi
}

# 创建远程目录
create_remote_dir() {
    log_step "创建远程目录..."

    ssh -o StrictHostKeyChecking=no \
        -o IdentityFile=~/.ssh/id_rsa_deploy \
        -o Port=$ECS_PORT \
        $ECS_USER@$ECS_HOST "mkdir -p $ECS_PATH"

    log_info "✓ 目录已创建: $ECS_PATH"
}

# 上传文件
upload_file() {
    log_step "上传文件..."

    # 使用 SCP 上传
    scp -o StrictHostKeyChecking=no \
        -o IdentityFile=~/.ssh/id_rsa_deploy \
        -o Port=$ECS_PORT \
        "$LOCAL_FILE" \
        $ECS_USER@$ECS_HOST:$ECS_PATH/

    log_info "✓ 文件已上传"
}

# 验证远程文件
verify_remote() {
    log_step "验证远程文件..."

    # 获取远程文件信息
    REMOTE_INFO=$(ssh -o StrictHostKeyChecking=no \
                       -o IdentityFile=~/.ssh/id_rsa_deploy \
                       -o Port=$ECS_PORT \
                       $ECS_USER@$ECS_HOST "ls -lh $ECS_PATH/domestic_llm_models.json 2>/dev/null" || echo "")

    if [ -n "$REMOTE_INFO" ]; then
        echo "$REMOTE_INFO"

        # 获取文件大小
        REMOTE_SIZE=$(echo "$REMOTE_INFO" | awk '{print $5}')
        LOCAL_SIZE=$(stat -f%z "$LOCAL_FILE" 2>/dev/null || stat -c%s "$LOCAL_FILE" 2>/dev/null)

        if [ -n "$REMOTE_SIZE" ] && [ -n "$LOCAL_SIZE" ]; then
            if [ "$REMOTE_SIZE" -eq "$LOCAL_SIZE" ]; then
                log_info "✅ 文件大小验证通过 ($LOCAL_SIZE bytes)"
            else
                log_warn "文件大小不匹配 (本地: $LOCAL_SIZE, 远程: $REMOTE_SIZE)"
            fi
        fi
    else
        log_error "无法验证远程文件"
        return 1
    fi
}

# 显示远程文件内容预览
show_remote_preview() {
    log_step "远程文件内容预览..."

    ssh -o StrictHostKeyChecking=no \
        -o IdentityFile=~/.ssh/id_rsa_deploy \
        -o Port=$ECS_PORT \
        $ECS_USER@$ECS_HOST "head -20 $ECS_PATH/domestic_llm_models.json"
}

# 清理
cleanup() {
    log_step "清理临时文件..."
    rm -f ~/.ssh/id_rsa_deploy ~/.ssh/known_hosts
}

# 主函数
main() {
    check_config
    show_config
    setup_ssh_key
    test_connection
    create_remote_dir
    upload_file
    verify_remote
    show_remote_preview
    cleanup

    echo ""
    echo "=========================================="
    log_info "🎉 部署完成!"
    echo "=========================================="
    echo ""
    echo "文件已上传到: $ECS_PATH/domestic_llm_models.json"
    echo "服务器: $ECS_USER@$ECS_HOST:$ECS_PORT"
}

# 捕获退出信号
trap cleanup EXIT

# 运行
main "$@"
