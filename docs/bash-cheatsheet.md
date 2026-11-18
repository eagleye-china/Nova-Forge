# Linux Bash 常用命令速查表

> 适用于大多数 Linux 发行版，默认 Shell 为 Bash。

---

## 一、文件与目录

| 命令 | 作用 | 常用示例 |
|---|---|---|
| `pwd` | 显示当前目录 | `pwd` |
| `ls` | 列出目录内容 | `ls -la` |
| `cd` | 切换目录 | `cd /etc`、`cd ~`、`cd ..` |
| `mkdir` | 新建目录 | `mkdir -p a/b/c` |
| `touch` | 新建空文件 | `touch note.txt` |
| `cp` | 复制 | `cp -r src/ dst/` |
| `mv` | 移动 / 重命名 | `mv a.txt b.txt` |
| `rm` | 删除 | `rm -rf dir/`（慎用） |
| `cat` | 查看文件全部内容 | `cat config.yml` |
| `less` | 分页查看大文件 | `less big.log` |
| `head` / `tail` | 查看开头 / 结尾 | `tail -f app.log` |

---

## 二、查看与文本处理

| 命令 | 作用 | 常用示例 |
|---|---|---|
| `grep` | 按关键字过滤 | `grep -rn "error" ./logs` |
| `wc` | 统计行数/字数 | `wc -l data.txt` |
| `sort` / `uniq` | 排序 / 去重 | `sort a.txt \| uniq -c` |
| `awk` | 按列提取 | `awk '{print $1, $3}' file` |
| `sed` | 流式替换 | `sed -i 's/old/new/g' file` |
| `find` | 查找文件 | `find /var/log -name "*.log"` |
| `which` / `whereis` | 查命令位置 | `which python3` |
| `echo` | 输出文本 / 变量 | `echo $PATH` |

---

## 三、系统与环境

| 命令 | 作用 | 常用示例 |
|---|---|---|
| `ps` | 查看进程 | `ps aux \| grep nginx` |
| `top` / `htop` | 实时监控 | `top` |
| `kill` | 结束进程 | `kill -9 PID` |
| `df` / `du` | 磁盘空间 | `df -h`、`du -sh ./dir` |
| `free` | 内存使用 | `free -h` |
| `uname` | 系统信息 | `uname -a` |
| `env` | 查看环境变量 | `env \| grep PATH` |
| `export` | 设置环境变量 | `export PATH=$PATH:~/bin` |
| `history` | 历史命令 | `history \| grep git` |
| `man` / `--help` | 查手册 | `man ls` |

---

## 四、权限与用户

| 命令 | 作用 | 常用示例 |
|---|---|---|
| `chmod` | 改权限 | `chmod +x run.sh`、`chmod 644 file` |
| `chown` | 改属主 | `sudo chown user:group file` |
| `sudo` | 管理员执行 | `sudo apt update` |
| `su` | 切换用户 | `su - root` |
| `id` / `whoami` | 查看当前用户 | `id` |

---

## 五、网络

| 命令 | 作用 | 常用示例 |
|---|---|---|
| `ping` | 测连通 | `ping -c 4 baidu.com` |
| `curl` | 请求接口 / 下载 | `curl -O https://x.com/f.tar.gz` |
| `wget` | 下载文件 | `wget -c url` |
| `ss` / `netstat` | 查看端口 | `ss -tlnp \| grep 8080` |
| `ssh` | 远程登录 | `ssh user@192.168.1.10` |
| `scp` | 跨机复制 | `scp file.txt user@host:/tmp/` |

---

## 六、压缩与打包

| 命令 | 作用 | 常用示例 |
|---|---|---|
| `tar` | 打包/解包 | `tar -czf a.tar.gz dir/`、`tar -xzf a.tar.gz -C /opt` |
| `zip` / `unzip` | zip 压缩 | `zip -r a.zip dir/`、`unzip a.zip` |

---

## 七、软件包安装

- **Debian / Ubuntu**：`sudo apt update && sudo apt install -y 包名`
- **CentOS / RHEL**：`sudo yum install -y 包名`（新版用 `dnf`）
- **Arch**：`sudo pacman -S 包名`

---

## 八、常用语法

| 写法 | 含义 |
|---|---|
| `\|` | 管道：把前一个命令输出交给后一个 |
| `>` | 覆盖写入 |
| `>>` | 追加写入 |
| `2>&1` | 错误输出也一起重定向 |
| `&&` | 前一条成功才执行后一条 |
| `*` `?` | 通配符：`*.log`、`?.txt` |
| `~` | 家目录 |
| `..` | 上一级目录 |
| `.` | 当前目录 |
| `!!` | 重复上一条命令 |

---

## 九、新手注意事项

1. **`rm -rf` 慎用**，删除前先 `ls` 确认路径。
2. **路径带空格要加引号**，如 `cd "My Folder"`。
3. **Tab 补全**：记不全路径时多按 Tab。
4. **Ctrl+C**：终止当前命令。
5. **Ctrl+L**：清屏。
6. **man 命令**：不确定用法时先 `man 命令` 或 `命令 --help`。

---

## 十、练习建议

1. 先练：`cd / ls / cp / mv / rm / mkdir / touch`
2. 再练：`grep / tail -f / ps / kill / find`
3. 最后补：`tar / chmod / ssh / awk / sed`
4. 每天在真实目录上敲一遍，一周形成肌肉记忆。