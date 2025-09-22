# A股多周期K线数据库设计方案

面对5000多支股票和7种不同周期的K线数据，我们需要一个高度优化且可扩展的数据库设计方案。以下是针对大规模数据的专业级解决方案。

## 总体架构设计

我推荐采用**分库分表 + 分区**的混合架构，具体如下：

1. **按股票代码范围分库**：将5000多支股票分散到多个数据库文件中
2. **按周期分表**：每个数据库中为不同周期创建单独的表
3. **按时间分区**：在每个周期表中使用时间分区优化查询性能

## 数据库分布策略

### 1. 按股票代码分库

将A股股票按代码前缀分布到多个数据库中，例如：

```
stocks_00.db  # 代码000000-009999
stocks_01.db  # 代码010000-019999
stocks_02.db  # 代码020000-029999
...
stocks_60.db  # 代码600000-609999
...
stocks_68.db  # 代码680000-689999
stocks_30.db  # 代码300000-309999
```

### 2. 按周期分表

每个数据库中包含7张表，对应不同周期：
- `kline_30min`
- `kline_60min`
- `kline_120min`
- `kline_day`
- `kline_2day`
- `kline_3day`
- `kline_week`

## 表结构设计

所有周期的表结构保持一致，便于统一管理：

```sql
-- 以30分钟线为例，其他周期表结构相同
CREATE TABLE kline_30min (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code VARCHAR(10) NOT NULL,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    open_price DECIMAL(12, 4) NOT NULL,
    high_price DECIMAL(12, 4) NOT NULL,
    low_price DECIMAL(12, 4) NOT NULL,
    close_price DECIMAL(12, 4) NOT NULL,
    volume BIGINT NOT NULL DEFAULT 0,
    turnover DECIMAL(20, 4) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 复合索引优化查询性能
    UNIQUE(stock_code, period_start),
    INDEX idx_stock_period (stock_code, period_start),
    INDEX idx_period_start (period_start)
);

-- 为其他周期创建相同的表结构
CREATE TABLE kline_60min (...);
CREATE TABLE kline_120min (...);
-- ... 其余周期
```

## 数据量估算与优化策略

### 数据量估算

以单支股票为例：
- 30分钟线：每日约13条（9:30-15:00，共4小时，8个30分钟周期，但A股中午休市，实际约6-7条）
- 年数据量：250交易日 × 7条/日 = 1,750条
- 7种周期总数据量：1,750 × 7 = 12,250条/年/股

5000支股票年数据总量：
- 5000 × 12,250 = 61,250,000条（约6100万条）

5年历史数据总量：
- 61,250,000 × 5 = 306,250,000条（约3亿条）

### 优化策略

1. **分区策略**：每年将旧数据归档到历史表
2. **索引优化**：精心设计复合索引，避免过度索引
3. **数据压缩**：对历史数据应用压缩算法
4. **缓存策略**：使用Redis等缓存热门股票数据

## 数据库管理类实现

以下是完整的数据库管理类实现：

```python
import sqlite3
import os
import threading
from datetime import datetime, timedelta
from queue import Queue

class AStockKlineDBManager:
    """A股多周期K线数据库管理类"""
    
    def __init__(self, base_dir="./stocks/db"):
        self.base_dir = base_dir
        self.db_connections = {}  # 数据库连接池
        self.lock = threading.RLock()
        self._ensure_directories()
        
    def _ensure_directories(self):
        """确保数据库目录存在"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
    
    def _get_db_name(self, stock_code):
        """根据股票代码确定数据库名称"""
        # 提取股票代码前缀
        prefix = stock_code[:2]
        return f"stocks_{prefix}.db"
    
    def _get_db_path(self, db_name):
        """获取数据库完整路径"""
        return os.path.join(self.base_dir, db_name)
    
    @contextmanager
    def _get_connection(self, stock_code):
        """获取数据库连接（带连接池）"""
        db_name = self._get_db_name(stock_code)
        db_path = self._get_db_path(db_name)
        
        with self.lock:
            if db_path not in self.db_connections:
                # 初始化连接池（最大5个连接）
                self.db_connections[db_path] = Queue(maxsize=5)
                for _ in range(3):
                    conn = sqlite3.connect(db_path, check_same_thread=False)
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    self.db_connections[db_path].put(conn)
            
            conn = self.db_connections[db_path].get()
            try:
                yield conn
            finally:
                self.db_connections[db_path].put(conn)
    
    def _init_db_tables(self, db_path):
        """初始化数据库表结构"""
        periods = ['30min', '60min', '120min', 'day', '2day', '3day', 'week']
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for period in periods:
                table_name = f"kline_{period}"
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stock_code VARCHAR(10) NOT NULL,
                        period_start DATETIME NOT NULL,
                        period_end DATETIME NOT NULL,
                        open_price DECIMAL(12, 4) NOT NULL,
                        high_price DECIMAL(12, 4) NOT NULL,
                        low_price DECIMAL(12, 4) NOT NULL,
                        close_price DECIMAL(12, 4) NOT NULL,
                        volume BIGINT NOT NULL DEFAULT 0,
                        turnover DECIMAL(20, 4) NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(stock_code, period_start)
                    )
                """)
                
                # 创建索引
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_stock_period 
                    ON {table_name}(stock_code, period_start)
                """)
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_period_start 
                    ON {table_name}(period_start)
                """)
            
            conn.commit()
    
    def save_kline_data(self, stock_code, period_type, kline_data):
        """保存K线数据"""
        table_name = f"kline_{period_type}"
        
        with self._get_connection(stock_code) as conn:
            cursor = conn.cursor()
            
            # 使用事务批量插入
            cursor.execute("BEGIN TRANSACTION")
            try:
                for data in kline_data:
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO {table_name}
                        (stock_code, period_start, period_end, open_price, high_price, low_price, close_price, volume, turnover)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        stock_code,
                        data['period_start'],
                        data['period_end'],
                        data['open_price'],
                        data['high_price'],
                        data['low_price'],
                        data['close_price'],
                        data['volume'],
                        data['turnover']
                    ))
                cursor.execute("COMMIT")
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
    
    def get_kline_data(self, stock_code, period_type, start_date, end_date):
        """获取K线数据"""
        table_name = f"kline_{period_type}"
        
        with self._get_connection(stock_code) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT period_start, period_end, open_price, high_price, low_price, close_price, volume, turnover
                FROM {table_name}
                WHERE stock_code = ? AND period_start >= ? AND period_start <= ?
                ORDER BY period_start
            """, (stock_code, start_date, end_date))
            
            return cursor.fetchall()
    
    def archive_old_data(self, years_to_keep=2):
        """归档旧数据"""
        cutoff_date = datetime.now() - timedelta(days=365 * years_to_keep)
        
        for db_name in os.listdir(self.base_dir):
            if db_name.endswith('.db'):
                db_path = os.path.join(self.base_dir, db_name)
                self._archive_db_data(db_path, cutoff_date)
    
    def _archive_db_data(self, db_path, cutoff_date):
        """归档单个数据库的旧数据"""
        periods = ['30min', '60min', '120min', 'day', '2day', '3day', 'week']
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            for period in periods:
                table_name = f"kline_{period}"
                archive_table_name = f"kline_{period}_archive"
                
                # 创建归档表（如果不存在）
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {archive_table_name} AS
                    SELECT * FROM {table_name} WHERE 1=0
                """)
                
                # 迁移旧数据到归档表
                cursor.execute(f"""
                    INSERT INTO {archive_table_name}
                    SELECT * FROM {table_name}
                    WHERE period_start < ?
                """, (cutoff_date,))
                
                # 删除原表中的旧数据
                cursor.execute(f"""
                    DELETE FROM {table_name}
                    WHERE period_start < ?
                """, (cutoff_date,))
            
            conn.commit()
    
    def close_all_connections(self):
        """关闭所有数据库连接"""
        with self.lock:
            for db_path, conn_pool in self.db_connections.items():
                while not conn_pool.empty():
                    try:
                        conn = conn_pool.get_nowait()
                        conn.close()
                    except:
                        pass
            self.db_connections.clear()

# 使用示例
if __name__ == "__main__":
    db_manager = AStockKlineDBManager()
    
    # 示例数据
    kline_data_30min = [
        {
            'period_start': '2023-06-01 09:30:00',
            'period_end': '2023-06-01 10:00:00',
            'open_price': 10.50,
            'high_price': 10.80,
            'low_price': 10.45,
            'close_price': 10.75,
            'volume': 1500000,
            'turnover': 15750000.00
        },
        # 更多数据...
    ]
    
    # 保存数据
    db_manager.save_kline_data('000001', '30min', kline_data_30min)
    
    # 查询数据
    data = db_manager.get_kline_data('000001', '30min', '2023-06-01', '2023-06-02')
    print(f"获取到 {len(data)} 条K线数据")
    
    # 程序退出时关闭连接
    db_manager.close_all_connections()
```

## 数据维护与优化策略

### 1. 定期归档
- 每年将超过2年的历史数据迁移到归档表
- 归档表可压缩存储或迁移到冷存储

### 2. 索引优化
- 定期分析查询模式，优化索引策略
- 使用`ANALYZE`命令更新数据库统计信息
- 重建碎片化索引

### 3. 数据验证
- 定期检查数据完整性
- 验证价格数据的合理性（如价格跳变检测）

### 4. 备份策略
- 每日增量备份
- 每周全量备份
- 备份文件压缩存储

## 性能优化建议

1. **批量操作**：使用事务批量插入数据，减少IO操作
2. **预编译语句**：对常用查询使用预编译SQL语句
3. **内存优化**：适当增加SQLite缓存大小
4. **连接池**：使用连接池管理数据库连接
5. **异步处理**：对数据更新操作使用异步队列

## 总结

这个设计方案通过分库分表策略有效管理了5000多支股票的7种周期K线数据，具有以下优点：

1. **可扩展性**：通过分库支持水平扩展
2. **性能优化**：通过分表和索引优化查询性能
3. **维护性**：通过定期归档保持主数据库轻量
4. **可靠性**：通过备份和验证策略确保数据安全

对于超大规模应用，未来还可以考虑：
1. 使用分布式数据库（如TiDB）替代SQLite
2. 引入列式存储优化分析查询
3. 使用内存数据库缓存热点数据