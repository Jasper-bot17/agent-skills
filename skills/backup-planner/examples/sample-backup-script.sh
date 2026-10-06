#!/bin/bash
# 自动生成的 tar 备份脚本
# 源目录：/home/user/data
# 生成时间：2026-10-02 20:30:00
# 用法：./backup.sh [目标目录]
#   默认目标：/backup

SOURCE="/home/user/data"
DEST="${1:-/backup}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}.tar.gz"
LOG_FILE="${DEST}/backup_${TIMESTAMP}.log"

echo "========================================"
echo "  备份开始"
echo "========================================"
echo "源目录：${SOURCE}"
echo "目标文件：${DEST}/${BACKUP_NAME}"
echo "开始时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查源目录
if [ ! -d "${SOURCE}" ]; then
    echo "❌ 错误：源目录不存在：${SOURCE}"
    exit 1
fi

# 检查目标目录
if [ ! -d "${DEST}" ]; then
    echo "⚠️  目标目录不存在，正在创建：${DEST}"
    mkdir -p "${DEST}"
fi

# 检查磁盘空间（至少需要源目录大小的 1.5 倍）
SOURCE_SIZE=$(du -sb "${SOURCE}" | cut -f1)
REQUIRED_SIZE=$((SOURCE_SIZE * 3 / 2))
AVAILABLE_SIZE=$(df -B1 "${DEST}" | tail -1 | awk '{print $4}')

if [ "${AVAILABLE_SIZE}" -lt "${REQUIRED_SIZE}" ]; then
    echo "❌ 错误：磁盘空间不足"
    echo "  需要：$((REQUIRED_SIZE / 1024 / 1024)) MB"
    echo "  可用：$((AVAILABLE_SIZE / 1024 / 1024)) MB"
    exit 1
fi

# 执行备份
echo "正在备份..."
tar -czf "${DEST}/${BACKUP_NAME}" \
    --exclude="node_modules" \
    --exclude=".git" \
    --exclude="__pycache__" \
    --exclude=".venv" \
    --exclude="venv" \
    --exclude="dist" \
    --exclude="build" \
    --exclude="*.log" \
    --exclude="*.tmp" \
    --exclude=".DS_Store" \
    --exclude="Thumbs.db" \
    -C "$(dirname "${SOURCE}")" \
    "$(basename "${SOURCE}")" 2>&1 | tee "${LOG_FILE}"

TAR_EXIT=$?

echo ""
if [ ${TAR_EXIT} -eq 0 ]; then
    BACKUP_SIZE=$(du -h "${DEST}/${BACKUP_NAME}" | cut -f1)
    echo "✅ 备份完成！"
    echo "  文件：${BACKUP_NAME}"
    echo "  大小：${BACKUP_SIZE}"
    echo "  日志：${LOG_FILE}"
    echo "  结束时间：$(date '+%Y-%m-%d %H:%M:%S')"

    # 生成校验和
    echo ""
    echo "正在生成校验和..."
    sha256sum "${DEST}/${BACKUP_NAME}" > "${DEST}/${BACKUP_NAME}.sha256"
    echo "  校验和：${DEST}/${BACKUP_NAME}.sha256"

    # 清理旧备份（保留最近 7 份）
    echo ""
    echo "清理旧备份（保留最近 7 份）..."
    cd "${DEST}" && ls -t backup_*.tar.gz 2>/dev/null | tail -n +8 | while read old; do
        rm -f "${old}" "${old}.sha256" "backup_$(echo ${old} | sed 's/backup_//;s/.tar.gz//').log"
        echo "  已删除：${old}"
    done

    echo ""
    echo "========================================"
    echo "  备份成功"
    echo "========================================"
    exit 0
else
    echo "❌ 备份失败（退出码：${TAR_EXIT}）"
    echo "  请查看日志：${LOG_FILE}"
    echo "========================================"
    echo "  备份失败"
    echo "========================================"
    exit 1
fi
