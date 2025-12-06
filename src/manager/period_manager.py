from enum import Enum

class TimePeriod(Enum):
    MINUTE_1 = '1m'
    MINUTE_3 = '3m'
    MINUTE_5 = '5m'
    MINUTE_10 = '10m'
    MINUTE_15 = '15m'
    MINUTE_30 = '30m'
    MINUTE_45 = '55m'
    MINUTE_60 = '60m'
    MINUTE_90 = '90m'
    MINUTE_120 = '120m'
    DAY = '1d'
    WEEK = '1w'
    MONTH = '1M'     # 暂无月线数据，使用日线替代
    QUARTER = '1Q'   # 暂无季线数据，使用日线替代
    YEAR = '1Y'      # 暂无年线数据，使用日线替代
    
    @classmethod
    def from_label(cls, label):
        """根据按钮标签获取对应的枚举值"""
        mapping = {
            "日线": cls.DAY,
            "周线": cls.WEEK,
            "月线": cls.MONTH,
            "季线": cls.QUARTER,
            "年线": cls.YEAR,
            "1分": cls.MINUTE_1,
            "3分": cls.MINUTE_3,
            "5分": cls.MINUTE_5,
            "10分": cls.MINUTE_10,
            "15分": cls.MINUTE_15,
            "30分": cls.MINUTE_30,
            "45分": cls.MINUTE_45,
            "60分": cls.MINUTE_60,
            "90分": cls.MINUTE_90,
            "120分": cls.MINUTE_120,
        }
        return mapping.get(label, cls.DAY)
    
    def get_table_name(self):
        """
        获取对应级别的数据库表名
        例如: '1d' -> 'stock_data_1d', '30m' -> 'stock_data_30m'
        """
        return f"stock_data_{self.value}"