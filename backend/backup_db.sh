#!/bin/bash
# bet365cn 数据库每日备份脚本
# 用法: 每日凌晨 cron 执行（postgres 用户）
# 输出: /opt/backups/bet365cn/bet365cn_YYYY-MM-DD.sql.gz
# 保留最近 30 天

BACKUP_DIR="/opt/backups/bet365cn"
DB_NAME="bet365cn"
RETENTION_DAYS=30
DATE=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

# pg_dump (postgres 用户直接本地连接)
pg_dump "$DB_NAME" | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ] && [ -s "$BACKUP_FILE" ]; then
    echo "[$(date)] OK: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
else
    echo "[$(date)] FAIL" >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

# 清理旧备份
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete
