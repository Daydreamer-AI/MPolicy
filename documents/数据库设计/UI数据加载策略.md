# UI数据加载策略：初始化预加载 vs. 按需动态加载

对于股票K线数据在UI中的使用，这是一个典型的**性能与资源消耗的权衡问题**。我的建议是采用**分层缓存策略**，而不是简单的二选一。

## 核心结论

**采用"按需加载 + 多层缓存"的混合策略**，具体来说：
1. **极短期数据**：初始化时预加载（如当前交易日的数据）
2. **常用范围数据**：按需加载并缓存（如最近3个月的数据）
3. **历史数据**：完全按需加载，使用后适当缓存

## 详细策略分析

### 为什么不推荐完全初始化加载？

1. **内存消耗过大**：
   - 5000支股票 × 7种周期 × 5年历史数据 ≈ 数GB内存
   - 会严重影响应用启动速度和整体性能

2. **数据利用率低**：
   - 用户通常只查看少数几只股票和有限时间范围
   - 大部分预加载的数据不会被使用

3. **实时性差**：
   - 初始化后新产生的数据需要额外机制更新

### 为什么不推荐完全按需加载？

1. **用户体验差**：
   - 每次切换股票或周期都有明显延迟
   - 频繁的数据库查询会影响整体性能

2. **重复计算**：
   - 相同数据可能被反复查询和计算

## 推荐的分层缓存实现方案

```python
import sqlite3
import threading
from datetime import datetime, timedelta
from collections import OrderedDict
import heapq

class KlineDataCacheManager:
    """K线数据缓存管理器"""
    
    def __init__(self, db_manager, max_memory_mb=500):
        self.db_manager = db_manager
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.current_memory_usage = 0
        
        # 使用有序字典实现LRU缓存
        self.cache = OrderedDict()
        self.cache_lock = threading.RLock()
        
        # 预加载配置
        self.preload_days = 1  # 预加载最近1天的数据
        self.cache_days = 90   # 缓存最近90天的数据
        
    def initialize(self):
        """初始化缓存管理器"""
        # 可以在后台线程预加载热门股票数据
        self._preload_hot_stocks_async()
    
    def _preload_hot_stocks_async(self):
        """异步预加载热门股票数据"""
        def preload_task():
            hot_stocks = ['000001', '399001', '000300']  # 上证指数、深证成指、沪深300
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.preload_days)
            
            for stock_code in hot_stocks:
                for period in ['30min', 'day']:
                    self.get_kline_data(stock_code, period, start_date, end_date)
        
        threading.Thread(target=preload_task, daemon=True).start()
    
    def get_kline_data(self, stock_code, period_type, start_date, end_date):
        """获取K线数据（带缓存）"""
        cache_key = f"{stock_code}_{period_type}_{start_date}_{end_date}"
        
        # 检查缓存
        with self.cache_lock:
            if cache_key in self.cache:
                # 更新LRU顺序
                data = self.cache.pop(cache_key)
                self.cache[cache_key] = data
                return data.copy()
        
        # 缓存未命中，从数据库查询
        data = self.db_manager.get_kline_data(stock_code, period_type, start_date, end_date)
        
        # 决定是否缓存
        should_cache = self._should_cache_data(stock_code, period_type, start_date, end_date)
        
        if should_cache:
            self._add_to_cache(cache_key, data)
        
        return data
    
    def _should_cache_data(self, stock_code, period_type, start_date, end_date):
        """判断是否应该缓存数据"""
        # 缓存最近90天的数据
        cache_cutoff = datetime.now() - timedelta(days=self.cache_days)
        return end_date >= cache_cutoff
    
    def _add_to_cache(self, key, data):
        """添加数据到缓存"""
        with self.cache_lock:
            # 估算数据内存占用
            data_size = self._estimate_memory_usage(data)
            
            # 如果缓存已满，移除最久未使用的项目
            while self.current_memory_usage + data_size > self.max_memory_bytes and self.cache:
                self._remove_oldest_from_cache()
            
            # 添加到缓存
            self.cache[key] = data
            self.current_memory_usage += data_size
    
    def _remove_oldest_from_cache(self):
        """移除最久未使用的缓存项"""
        if self.cache:
            key, data = self.cache.popitem(last=False)
            data_size = self._estimate_memory_usage(data)
            self.current_memory_usage -= data_size
    
    def _estimate_memory_usage(self, data):
        """估算数据内存占用（简化实现）"""
        # 每条记录约200字节
        return len(data) * 200
    
    def clear_cache(self):
        """清空缓存"""
        with self.cache_lock:
            self.cache.clear()
            self.current_memory_usage = 0
    
    def get_cache_info(self):
        """获取缓存信息"""
        with self.cache_lock:
            return {
                'cache_size': len(self.cache),
                'memory_usage_mb': self.current_memory_usage / (1024 * 1024),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024)
            }
```

## UI数据加载策略实现

```python
class UIKlineDataProvider:
    """UI数据提供器"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.current_requests = {}
        self.request_lock = threading.RLock()
    
    def request_kline_data(self, stock_code, period_type, date_range, callback):
        """
        请求K线数据
        
        参数:
            stock_code: 股票代码
            period_type: 周期类型
            date_range: (start_date, end_date) 元组
            callback: 数据就绪后的回调函数
        """
        request_id = f"{stock_code}_{period_type}_{date_range[0]}_{date_range[1]}"
        
        # 检查是否已有相同请求
        with self.request_lock:
            if request_id in self.current_requests:
                # 已有相同请求，只需添加回调
                self.current_requests[request_id]['callbacks'].append(callback)
                return
            
            # 创建新请求
            self.current_requests[request_id] = {
                'callbacks': [callback],
                'completed': False,
                'data': None
            }
        
        # 在后台线程获取数据
        def fetch_data():
            try:
                data = self.cache_manager.get_kline_data(
                    stock_code, period_type, date_range[0], date_range[1]
                )
                
                with self.request_lock:
                    self.current_requests[request_id]['completed'] = True
                    self.current_requests[request_id]['data'] = data
                    
                    # 执行所有回调
                    for cb in self.current_requests[request_id]['callbacks']:
                        try:
                            cb(data)
                        except Exception as e:
                            print(f"Callback error: {e}")
                    
                    # 清理已完成请求（保留一段时间以供后续相同请求使用）
                    # 实际中可以设置超时清理机制
            
            except Exception as e:
                print(f"Error fetching data: {e}")
                # 错误处理
        
        threading.Thread(target=fetch_data, daemon=True).start()
    
    def cancel_request(self, stock_code, period_type, date_range, callback=None):
        """取消数据请求"""
        request_id = f"{stock_code}_{period_type}_{date_range[0]}_{date_range[1]}"
        
        with self.request_lock:
            if request_id in self.current_requests:
                if callback:
                    # 移除特定回调
                    if callback in self.current_requests[request_id]['callbacks']:
                        self.current_requests[request_id]['callbacks'].remove(callback)
                    
                    # 如果没有其他回调，移除整个请求
                    if not self.current_requests[request_id]['callbacks']:
                        del self.current_requests[request_id]
                else:
                    # 移除整个请求
                    del self.current_requests[request_id]
```

## 实际应用中的优化建议

### 1. 数据粒度优化
```python
# 根据UI显示需求调整数据粒度
def get_optimized_kline_data(self, stock_code, period_type, start_date, end_date, max_points=500):
    """
    获取优化后的K线数据，确保返回点数不超过限制
    
    对于长时间范围的历史数据，自动进行降采样
    """
    # 计算所需数据点数
    total_days = (end_date - start_date).days
    expected_points = self._calculate_expected_points(period_type, total_days)
    
    if expected_points <= max_points:
        # 数据量适中，直接返回
        return self.get_kline_data(stock_code, period_type, start_date, end_date)
    else:
        # 数据量过大，需要进行降采样
        return self._get_downsampled_data(stock_code, period_type, start_date, end_date, max_points)
```

### 2. 预加载策略
```python
def preload_common_scenarios(self):
    """预加载常见使用场景的数据"""
    common_scenarios = [
        # (股票代码, 周期类型, 时间范围)
        ('000001', 'day', (datetime.now() - timedelta(days=30), datetime.now())),
        ('000001', '30min', (datetime.now() - timedelta(days=7), datetime.now())),
        ('399001', 'day', (datetime.now() - timedelta(days=30), datetime.now())),
        # 更多常见场景...
    ]
    
    for scenario in common_scenarios:
        self.cache_manager.get_kline_data(*scenario)
```

### 3. 内存管理
```python
def monitor_and_adjust_cache(self):
    """监控和调整缓存策略"""
    while True:
        cache_info = self.cache_manager.get_cache_info()
        
        # 根据内存使用情况调整缓存策略
        if cache_info['memory_usage_mb'] > cache_info['max_memory_mb'] * 0.8:
            # 内存使用超过80%，清理部分缓存
            self.cache_manager.clear_old_cache()
        
        # 休眠一段时间后再次检查
        time.sleep(60)  # 每分钟检查一次
```

## 总结

对于你的A股K线数据UI展示需求，推荐采用以下策略：

1. **按需加载为主**：避免一次性加载所有数据
2. **智能缓存为辅**：对常用数据建立多层缓存机制
3. **预加载优化体验**：对热门股票和常见场景预加载
4. **内存管理**：实现缓存淘汰和内存监控机制

这种混合策略能够在保证用户体验的同时，有效控制内存使用，适应不同使用场景的需求。实际实现时，可以根据具体的使用模式和用户行为数据进一步优化缓存策略和预加载规则。