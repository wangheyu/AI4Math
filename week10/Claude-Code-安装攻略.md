# Claude Code 国内安装与配置攻略

本攻略面向初学者，在国内网络环境下完成 Claude Code 的安装与配置。

---

## 1. 系统准备

```bash
sudo apt update
sudo apt install -y curl ca-certificates git bash
```

## 2. 安装 nvm（Node 版本管理器）

从 Gitee 镜像安装 nvm：

```bash
NVM_SOURCE=https://gitee.com/mirrors/nvm.git bash -c "$(curl -fsSL https://gitee.com/mirrors/nvm/raw/master/install.sh)"
```

安装完成后，在 `~/.bashrc` 末尾添加国内 Node.js 镜像源和 nvm 初始化：

```bash
# nvm 初始化
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# 使用 npmmirror 镜像加速 Node.js 下载
export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node
```

> **说明**：`io.js` 已合并回 Node.js，无需额外配置 `NVM_IOJS_ORG_MIRROR`。

使配置生效：

```bash
source ~/.bashrc
```

## 3. 安装 Node.js（LTS 版本）

```bash
nvm install --lts
```

验证安装：

```bash
node --version   # 应显示 v22.x 或 v24.x
npm --version    # 应显示 10.x
```

## 4. 配置 npm 国内镜像

```bash
npm config set registry https://registry.npmmirror.com/
```

验证配置：

```bash
npm config get registry
# 应输出：https://registry.npmmirror.com/
```

## 5. 安装 Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

验证安装：

```bash
claude --version
```

## 6. 获取 API Key

Claude Code 需要连接 API 服务。国内推荐以下两个平台，任选其一注册并获取 Key。

### DeepSeek

1. 访问 [platform.deepseek.com](https://platform.deepseek.com)
2. 注册账号（支持手机号）
3. 进入控制台 → 「API Keys」→ 创建 Key → 复制保存

### 通义千问（阿里云百炼）

1. 访问 [bailian.console.aliyun.com](https://bailian.console.aliyun.com)
2. 注册阿里云账号，开通「模型服务灵积」或「百炼」
3. 进入「API-KEY 管理」→ 创建 Key → 复制保存

> **注意**：Key 只显示一次，请立即保存到安全位置。两个平台新用户通常有免费额度。

---

## 7. 配置 API 服务商

拿到 Key 后，配置 Claude Code 连接服务商。

### 方案 A：DeepSeek

创建配置文件 `~/.config/secrets/anthropic-deepseek.env`：

```bash
export ANTHROPIC_AUTH_TOKEN="你的-deepseek-api-key"
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-pro
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export CLAUDE_CODE_EFFORT_LEVEL=max
```

### 方案 B：通义千问（阿里云 DashScope）

创建配置文件 `~/.config/secrets/anthropic-qianwen.env`：

```bash
export ANTHROPIC_AUTH_TOKEN="你的-qianwen-api-key"
export ANTHROPIC_BASE_URL="https://dashscope.aliyuncs.com/apps/anthropic"
export ANTHROPIC_MODEL=qwen3.6-plus
export ANTHROPIC_DEFAULT_OPUS_MODEL=qwen3.6-max-preview
export CLAUDE_CODE_SUBAGENT_MODEL=qwen3.6-plus
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export CLAUDE_CODE_EFFORT_LEVEL=max
```

### 加载配置

在 `~/.bashrc` 末尾添加：

```bash
# Claude Code 配置
[ -L ~/.config/secrets/anthropic-current.env ] && source ~/.config/secrets/anthropic-current.env

alias claude-fkit='claude --dangerously-skip-permissions'
```

然后手工选择要使用的服务商：

```bash
# 首次使用，二选一建立软链接：
ln -sfn ~/.config/secrets/anthropic-deepseek.env ~/.config/secrets/anthropic-current.env

# 或
ln -sfn ~/.config/secrets/anthropic-qianwen.env ~/.config/secrets/anthropic-current.env

source ~/.bashrc
```

### 便捷切换服务商（可选）

在 `~/.bashrc` 中添加以下函数，之后可用 `ai-switch` 命令快速切换：

```bash
ai-switch() {
    local dir="$HOME/.config/secrets"
    local link="$dir/anthropic-current.env"
    case "$1" in
        qianwen|deepseek)
            if [ ! -f "$dir/anthropic-$1.env" ]; then
                echo "error: $dir/anthropic-$1.env not found" >&2
                return 1
            fi
            unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL \
                  ANTHROPIC_DEFAULT_HAIKU_MODEL ANTHROPIC_DEFAULT_OPUS_MODEL \
                  ANTHROPIC_DEFAULT_SONNET_MODEL ANTHROPIC_MODEL \
                  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC CLAUDE_CODE_EFFORT_LEVEL \
                  CLAUDE_CODE_SUBAGENT_MODEL
            ln -sfn "anthropic-$1.env" "$link"
            source "$link"
            echo "✓ switched to $1"
            ;;
        ""|status)
            echo "current: $(readlink "$link" 2>/dev/null || echo '<unset>')"
            ;;
        *)
            echo "usage: ai-switch [qianwen|deepseek|status]" >&2
            return 1
            ;;
    esac
}
```

用法：

```bash
ai-switch deepseek    # 切换到 DeepSeek
ai-switch qianwen     # 切换到通义千问
ai-switch             # 查看当前服务商
```

## 8. 启动 Claude Code

```bash
claude
```

进入交互界面后，用自然语言描述你的开发任务即可。

---

## 9. 快捷方式：通过预配 WSL 镜像快速上手

如果不想手动安装，可以直接导入已配置好的 WSL 镜像。

### 下载镜像

| 镜像文件 | 说明 | 链接 |
|----------|------|------|
| Debian-start.tar | 纯净 Debian 系统 | [夸克网盘](https://pan.quark.cn/s/a04a7f19781a) |
| Debian-claude-ready.tar | 已装好 Claude Code，预配 DeepSeek + 千问 env | [夸克网盘](https://pan.quark.cn/s/588a149f06b5) |

### 导入（PowerShell）

```powershell
wsl --import TEST C:\wsl\TEST C:\Downloads\Debian-start.tar
```

参数说明：`wsl --import <发行版名称> <安装路径> <tar文件路径>`

### 配置默认用户

导入后进入的是 root 账户，需要设置默认用户。在 WSL 中编辑 `/etc/wsl.conf`：

```ini
[user]
default=newbie
```

> 预配镜像中默认账户用户名和密码均为 `newbie`。

重启 WSL 后生效：

```powershell
wsl --shutdown
wsl -d TEST
```

### 启动 Claude Code

```bash
claude
```

即可开始使用。

## 常见问题

**Q: `nvm install --lts` 下载很慢？**
确认 `NVM_NODEJS_ORG_MIRROR` 已正确设置，可尝试换用中科大镜像：
```bash
export NVM_NODEJS_ORG_MIRROR=https://mirrors.ustc.edu.cn/node/
```

**Q: `claude` 命令找不到？**
确认 npm 全局安装路径在 `PATH` 中，或重新执行 `source ~/.bashrc`。

**Q: 启动后连接失败？**
检查 `ANTHROPIC_BASE_URL` 是否正确指向服务商地址，确认 API Key 未过期。
