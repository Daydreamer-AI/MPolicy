
import json
from pathlib import Path
from typing import Dict, Any, Optional
from manager.logging_manager import get_logger

def color_to_hex(color):
    """
    将RGB/RGBA颜色元组转换为十六进制颜色字符串
    
    Args:
        color: RGB颜色元组，格式为 (r, g, b) 或 RGBA颜色元组，格式为 (r, g, b, a)
               其中每个值范围为0-255
    
    Returns:
        str: 十六进制颜色字符串，格式为 '#rrggbb' 或 '#rrggbbaa'
    """
    if isinstance(color, (tuple, list)):
        if len(color) == 3:
            # RGB 格式
            r, g, b = color
            return f"#{r:02x}{g:02x}{b:02x}"
        elif len(color) == 4:
            # RGBA 格式
            r, g, b, a = color
            return f"#{r:02x}{g:02x}{b:02x}{a:02x}"
        else:
            raise ValueError("颜色必须是包含3个或4个整数的元组或列表，格式为(r, g, b)或(r, g, b, a)")
    else:
        raise ValueError("颜色必须是元组或列表")


def hex_to_color(hex_color):
    """
    将十六进制颜色字符串转换为RGB/RGBA颜色元组
    
    Args:
        hex_color: 十六进制颜色字符串，格式为 '#rrggbb' 或 '#rrggbbaa' 或 'rrggbb' 或 'rrggbbaa'
    
    Returns:
        tuple: RGB颜色元组，格式为 (r, g, b) 或 RGBA颜色元组，格式为 (r, g, b, a)
    """
    # 移除可能存在的 # 符号
    hex_color = hex_color.lstrip('#')
    
    # 验证十六进制颜色格式
    if len(hex_color) not in (6, 8):
        raise ValueError("十六进制颜色必须是6位或8位字符，格式为 #rrggbb 或 #rrggbbaa")
    
    try:
        if len(hex_color) == 6:
            # RGB 格式
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b)
        elif len(hex_color) == 8:
            # RGBA 格式
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
            return (r, g, b, a)
    except ValueError:
        raise ValueError("无效的十六进制颜色字符串")
    
# 示例用法：
# RGB 颜色转换
# rgb_color = (255, 61, 61)
# hex_color = color_to_hex(rgb_color)  # 返回 '#ff3d3d'
# back_to_rgb = hex_to_color(hex_color)  # 返回 (255, 61, 61)

# RGBA 颜色转换（带透明度）
# rgba_color = (255, 61, 61, 128)  # 最后一个值是透明度，128表示半透明
# hex_color_with_alpha = color_to_hex(rgba_color)  # 返回 '#ff3d3d80'
# back_to_rgba = hex_to_color(hex_color_with_alpha)  # 返回 (255, 61, 61, 128)


# k线涨跌幅颜色
dict_kline_color = {
'desc': (0, 168, 67), #绿色－下跌 (0, 169, 178), (0, 168, 67), (43, 186, 146)
'asc': (255, 61, 61) #红色 -上涨
}

dict_kline_color_hex = {
'desc': '#00a84b', #绿色－下跌
'asc': '#ff3d3d' #红色 -上涨
}


# 均线
# 默认颜色
dict_ma_color = {
'ma5': (0, 0, 0), 
'ma10': (217, 186, 38), 
'ma20': (25, 160, 255), 
'ma24': (239, 57, 178),
'ma30': (255, 154, 117),
'ma52': (10, 204, 90),
'ma60': (119, 60, 178),
'ma120': (176, 187, 242),
'ma250': (175, 117, 234)
}

dict_ma_color_hex = {
    'ma5': '#000000', 
    'ma10': '#d9ba26', 
    'ma20': '#1fa0ff', 
    'ma24': '#ef39ae',
    'ma30': '#ff9a75',
    'ma52': '#0acc5a',
    'ma60': '#7777ff',
    'ma120': '#afafef',
    'ma250': '#af77ef'
}

class MASetting():
    def __init__(self, id=0, period=5, visible=True, line_width=2, color=(0, 0, 0), color_hex='#000000'):
        self.id = id
        self.period = period
        self.name = f"ma{period}"
        self.visible = visible
        self.line_width = line_width
        self.color = color
        self.color_hex = color_hex

    def set_color(self, color):
        self.color = color
        self.color_hex = color_to_hex(color)

    def set_color_hex(self, color_hex):
        self.color = hex_to_color(color_hex)
        self.color_hex = color_hex

dict_ma_setting_default = { 
    0: MASetting(0, 5, True, 2, dict_ma_color['ma5'], dict_ma_color_hex['ma5']),
    1: MASetting(1, 10, True, 2, dict_ma_color['ma10'], dict_ma_color_hex['ma10']),
    2: MASetting(2, 20, False, 2, dict_ma_color['ma20'], dict_ma_color_hex['ma20']),
    3: MASetting(3, 24, True, 2, dict_ma_color['ma24'], dict_ma_color_hex['ma24']),
    4: MASetting(4, 30, False, 2, dict_ma_color['ma30'], dict_ma_color_hex['ma30']),
    5: MASetting(5, 52, True, 2, dict_ma_color['ma52'], dict_ma_color_hex['ma52']),
    6: MASetting(6, 60, False, 2, dict_ma_color['ma60'], dict_ma_color_hex['ma60']),
    7: MASetting(7, 120, False, 2, dict_ma_color['ma120'], dict_ma_color_hex['ma120']),
    8: MASetting(8, 250, False, 2, dict_ma_color['ma250'], dict_ma_color_hex['ma250'])
}


# 用户自定义颜色
dict_ma_setting_user = dict_ma_setting_default.copy()


# 成交量
dict_volume_color = {
'ma5': dict_ma_color['ma5'],
'ma10': dict_ma_color['ma10'],
'ma20': dict_ma_color['ma20']
}

dict_volume_color_hex = {
    'ma5': dict_ma_color_hex['ma5'],
    'ma10': dict_ma_color_hex['ma10'],
    'ma20': dict_ma_color_hex['ma20']
}

dict_volume_color_user = dict_volume_color.copy()
dict_volume_color_user_hex = dict_volume_color_hex.copy()



# 成交额
dict_amount_color = {
'ma5': dict_ma_color['ma5'],
'ma10': dict_ma_color['ma10'],
'ma20': dict_ma_color['ma20']
}

dict_amount_color_hex = {
    'ma5': dict_ma_color_hex['ma5'],
    'ma10': dict_ma_color_hex['ma10'],
    'ma20': dict_ma_color_hex['ma20']
}

dict_amount_color_user = dict_amount_color.copy()
dict_amount_color_user_hex = dict_amount_color_hex.copy()


# MACD
dict_macd_color = {
'diff': (0, 0, 0),
'dea': (217, 186, 38),
}

dict_macd_color_hex = {
    'diff': '#000000',
    'dea': '#d9ba26'
}

dict_macd_color_user = dict_macd_color.copy()
dict_macd_color_user_hex = dict_macd_color_hex.copy()

# KDJ
dict_kdj_color = { 
'k': (217, 186, 38),
'd': (25, 160, 255),
'j': (244, 134, 208)
}

dict_kdj_color_hex = { 
    'k': '#d9ba26',
    'd': '#1fa0ff',
    'j': '#ef39ae'
}

dict_kdj_color_user = dict_kdj_color.copy()
dict_kdj_color_user_hex = dict_kdj_color_hex.copy()

# RSI
dict_rsi_color = { 
'rsi1': (217, 186, 38),
'rsi2': (10, 204, 90),
'rsi3': (25, 160, 255)
}

dict_rsi_color_hex = { 
    'rsi1': '#d9ba26',
    'rsi2': '#0acc5a',
    'rsi3': '#1fa0ff'
}

dict_rsi_color_user = dict_rsi_color.copy()
dict_rsi_color_user_hex = dict_rsi_color_hex.copy()

# BOLL
dict_boll_color = { 
'up': (255, 61, 61),
'mid': (25, 160, 255),
'down': (10, 204, 90),
'close': (0, 0, 0)
}

dict_boll_color_hex = { 
    'up': '#ff3d3d',
    'mid': '#1fa0ff',
    'down': '#0acc5a',
    'close': '#000000'
}

dict_boll_color_user = dict_boll_color.copy()
dict_boll_color_user_hex = dict_boll_color_hex.copy()


# -------------------------------------------------------------


class IndicatorSetting:
    """通用指标设置基类"""
    def __init__(self, name: str, visible: bool = True):
        self.name = name
        self.visible = visible

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式用于序列化"""
        return {
            'name': self.name,
            'visible': self.visible
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        instance = cls(data['name'], data.get('visible', True))
        return instance


class MASetting(IndicatorSetting):
    """均线设置"""
    def __init__(self, id: int = 0, period: int = 5, visible: bool = True, 
                 line_width: int = 2, color: tuple = (0, 0, 0), color_hex: str = '#000000'):
        super().__init__(f"ma{period}", visible)
        self.id = id
        self.period = period
        self.line_width = line_width
        self.color = color
        self.color_hex = color_hex

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'period': self.period,
            'name': self.name,
            'visible': self.visible,
            'line_width': self.line_width,
            'color': list(self.color),
            'color_hex': self.color_hex
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        instance = cls(
            id=data['id'],
            period=data['period'],
            visible=data.get('visible', True),
            line_width=data.get('line_width', 2),
            color=tuple(data['color']),
            color_hex=data['color_hex']
        )
        return instance


class ColorSetting(IndicatorSetting):
    """颜色设置基类"""
    def __init__(self, name: str, colors: Dict[str, tuple], color_hexes: Dict[str, str], visible: bool = True):
        super().__init__(name, visible)
        self.colors = colors  # RGB格式
        self.color_hexes = color_hexes  # 十六进制格式

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'visible': self.visible,
            'colors': {k: list(v) for k, v in self.colors.items()},
            'color_hexes': self.color_hexes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        instance = cls(
            name=data['name'],
            colors={k: tuple(v) for k, v in data['colors'].items()},
            color_hexes=data['color_hexes'],
            visible=data.get('visible', True)
        )
        return instance


class VolumeSetting(ColorSetting):
    """成交量设置"""
    pass


class AmountSetting(ColorSetting):
    """成交额设置"""
    pass


class MACDSetting(ColorSetting):
    """MACD设置"""
    pass


class KDJSetting(ColorSetting):
    """KDJ设置"""
    pass


class RSISetting(ColorSetting):
    """RSI设置"""
    pass


class BOLLSetting(ColorSetting):
    """BOLL设置"""
    pass


class IndicatorConfigManager:
    """指标配置管理器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_dir = Path.home() / '.config' / 'MPolicy'
        self.default_config_file = self.config_dir / 'indicator_config_default.json'
        self.user_config_file = self.config_dir / 'indicator_config_user.json'
        
        # 存储所有配置
        self.default_configs = {}  # 默认配置
        self.user_configs = {}     # 用户配置
        
        # 初始化默认配置
        self._init_default_configs()
    
    def _init_default_configs(self):
        """初始化默认配置"""
        # 从 indicators_config_manager.py 中导入的默认值
        from .indicators_config_manager import (
            dict_ma_color, dict_ma_color_hex, 
            dict_volume_color, dict_volume_color_hex,
            dict_amount_color, dict_amount_color_hex,
            dict_macd_color, dict_macd_color_hex,
            dict_kdj_color, dict_kdj_color_hex,
            dict_rsi_color, dict_rsi_color_hex,
            dict_boll_color, dict_boll_color_hex
        )
        
        # 默认均线配置
        self.default_configs['ma'] = {
            0: MASetting(0, 5, True, 2, dict_ma_color['ma5'], dict_ma_color_hex['ma5']),
            1: MASetting(1, 10, True, 2, dict_ma_color['ma10'], dict_ma_color_hex['ma10']),
            2: MASetting(2, 20, False, 2, dict_ma_color['ma20'], dict_ma_color_hex['ma20']),
            3: MASetting(3, 24, True, 2, dict_ma_color['ma24'], dict_ma_color_hex['ma24']),
            4: MASetting(4, 30, False, 2, dict_ma_color['ma30'], dict_ma_color_hex['ma30']),
            5: MASetting(5, 52, True, 2, dict_ma_color['ma52'], dict_ma_color_hex['ma52']),
            6: MASetting(6, 60, False, 2, dict_ma_color['ma60'], dict_ma_color_hex['ma60']),
            7: MASetting(7, 120, False, 2, dict_ma_color['ma120'], dict_ma_color_hex['ma120']),
            8: MASetting(8, 250, False, 2, dict_ma_color['ma250'], dict_ma_color_hex['ma250'])
        }
        
        # 其他指标默认配置
        self.default_configs['volume'] = {
            'default': VolumeSetting('volume', dict_volume_color, dict_volume_color_hex)
        }
        
        self.default_configs['amount'] = {
            'default': AmountSetting('amount', dict_amount_color, dict_amount_color_hex)
        }
        
        self.default_configs['macd'] = {
            'default': MACDSetting('macd', dict_macd_color, dict_macd_color_hex)
        }
        
        self.default_configs['kdj'] = {
            'default': KDJSetting('kdj', dict_kdj_color, dict_kdj_color_hex)
        }
        
        self.default_configs['rsi'] = {
            'default': RSISetting('rsi', dict_rsi_color, dict_rsi_color_hex)
        }
        
        self.default_configs['boll'] = {
            'default': BOLLSetting('boll', dict_boll_color, dict_boll_color_hex)
        }
        
        # 初始化用户配置为空
        for indicator_type in self.default_configs:
            self.user_configs[indicator_type] = {}
    
    def save_default_config(self):
        """保存默认配置到文件"""
        try:
            config_data = {}
            for indicator_type, settings in self.default_configs.items():
                config_data[indicator_type] = {}
                for key, setting in settings.items():
                    config_data[indicator_type][str(key)] = setting.to_dict()
            
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.default_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存默认配置失败: {e}")
    
    def save_user_config(self):
        """保存用户配置到文件"""
        try:
            config_data = {}
            for indicator_type, settings in self.user_configs.items():
                config_data[indicator_type] = {}
                for key, setting in settings.items():
                    config_data[indicator_type][str(key)] = setting.to_dict()
            
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存用户配置失败: {e}")
    
    def load_default_config(self):
        """从文件加载默认配置"""
        if not self.default_config_file.exists():
            return False
        
        try:
            with open(self.default_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.default_configs = self._deserialize_config(config_data)
            return True
        except Exception as e:
            self.logger.error(f"加载默认配置失败: {e}")
            return False
    
    def load_user_config(self):
        """从文件加载用户配置"""
        if not self.user_config_file.exists():
            # 用户配置不存在，使用默认配置初始化
            self._init_user_configs_from_defaults()
            return False
        
        try:
            with open(self.user_config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.user_configs = self._deserialize_config(config_data)
            return True
        except Exception as e:
            self.logger.error(f"加载用户配置失败: {e}")
            # 加载失败时使用默认配置初始化
            self._init_user_configs_from_defaults()
            return False
    
    def _deserialize_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """反序列化配置数据"""
        result = {}
        
        for indicator_type, settings in config_data.items():
            result[indicator_type] = {}
            for key_str, setting_data in settings.items():
                # 根据配置类型创建相应的对象
                if indicator_type == 'ma':
                    setting = MASetting.from_dict(setting_data)
                elif indicator_type in ['volume', 'amount', 'macd', 'kdj', 'rsi', 'boll']:
                    # 使用通用的颜色设置类
                    if indicator_type == 'volume':
                        setting = VolumeSetting.from_dict(setting_data)
                    elif indicator_type == 'amount':
                        setting = AmountSetting.from_dict(setting_data)
                    elif indicator_type == 'macd':
                        setting = MACDSetting.from_dict(setting_data)
                    elif indicator_type == 'kdj':
                        setting = KDJSetting.from_dict(setting_data)
                    elif indicator_type == 'rsi':
                        setting = RSISetting.from_dict(setting_data)
                    elif indicator_type == 'boll':
                        setting = BOLLSetting.from_dict(setting_data)
                else:
                    # 未知类型，使用基础设置类
                    setting = IndicatorSetting.from_dict(setting_data)
                
                result[indicator_type][int(key_str) if key_str.isdigit() else key_str] = setting
        
        return result
    
    def _init_user_configs_from_defaults(self):
        """从默认配置初始化用户配置"""
        for indicator_type, default_settings in self.default_configs.items():
            self.user_configs[indicator_type] = {}
            for key, setting in default_settings.items():
                # 深拷贝默认设置
                if isinstance(setting, MASetting):
                    self.user_configs[indicator_type][key] = MASetting(
                        id=setting.id,
                        period=setting.period,
                        visible=setting.visible,
                        line_width=setting.line_width,
                        color=setting.color,
                        color_hex=setting.color_hex
                    )
                    self.user_configs[indicator_type][key].name = setting.name
                else:
                    # 对于颜色设置类型
                    self.user_configs[indicator_type][key] = setting.__class__(
                        name=setting.name,
                        colors=setting.colors.copy(),
                        color_hexes=setting.color_hexes.copy(),
                        visible=setting.visible
                    )
    
    def get_indicator_settings(self, indicator_type: str, user_id: str = 'default') -> Dict:
        """获取指定类型的指标设置"""
        if indicator_type in self.user_configs and user_id in self.user_configs[indicator_type]:
            return self.user_configs[indicator_type][user_id]
        elif indicator_type in self.default_configs:
            return self.default_configs[indicator_type]
        else:
            return {}
    
    def set_indicator_settings(self, indicator_type: str, settings: Dict, user_id: str = 'default'):
        """设置指定类型的指标配置"""
        if indicator_type not in self.user_configs:
            self.user_configs[indicator_type] = {}
        self.user_configs[indicator_type][user_id] = settings
    
    def reset_to_defaults(self, indicator_type: str = None, user_id: str = 'default'):
        """重置为默认设置"""
        if indicator_type:
            # 重置特定指标类型
            if indicator_type in self.default_configs:
                self.user_configs[indicator_type] = {}
                for key, setting in self.default_configs[indicator_type].items():
                    if isinstance(setting, MASetting):
                        new_setting = MASetting(
                            id=setting.id,
                            period=setting.period,
                            visible=setting.visible,
                            line_width=setting.line_width,
                            color=setting.color,
                            color_hex=setting.color_hex
                        )
                        new_setting.name = setting.name
                        self.user_configs[indicator_type][key] = new_setting
                    else:
                        new_setting = setting.__class__(
                            name=setting.name,
                            colors=setting.colors.copy(),
                            color_hexes=setting.color_hexes.copy(),
                            visible=setting.visible
                        )
                        self.user_configs[indicator_type][key] = new_setting
        else:
            # 重置所有指标类型
            self._init_user_configs_from_defaults()
    
    def add_indicator_type(self, indicator_type: str, default_settings: Dict):
        """添加新的指标类型"""
        self.default_configs[indicator_type] = default_settings
        self.user_configs[indicator_type] = {}
        self._init_user_configs_from_defaults()
    
    def get_all_indicator_types(self) -> list:
        """获取所有指标类型"""
        return list(self.default_configs.keys())


# 全局实例
_indicator_config_manager = None

def get_indicator_config_manager() -> IndicatorConfigManager:
    """获取指标配置管理器实例"""
    global _indicator_config_manager
    if _indicator_config_manager is None:
        _indicator_config_manager = IndicatorConfigManager()
    return _indicator_config_manager


# 便捷函数
def load_indicator_configs():
    """加载所有指标配置"""
    manager = get_indicator_config_manager()
    manager.load_default_config()
    manager.load_user_config()


def save_indicator_configs():
    """保存所有指标配置"""
    manager = get_indicator_config_manager()
    manager.save_default_config()
    manager.save_user_config()


def get_ma_settings(user_id: str = 'default') -> Dict:
    """获取均线设置"""
    manager = get_indicator_config_manager()
    return manager.get_indicator_settings('ma', user_id)


def get_volume_settings(user_id: str = 'default') -> Dict:
    """获取成交量设置"""
    manager = get_indicator_config_manager()
    return manager.get_indicator_settings('volume', user_id)


def get_macd_settings(user_id: str = 'default') -> Dict:
    """获取MACD设置"""
    manager = get_indicator_config_manager()
    return manager.get_indicator_settings('macd', user_id)


def reset_indicator_configs(indicator_type: str = None):
    """重置指标配置"""
    manager = get_indicator_config_manager()
    manager.reset_to_defaults(indicator_type)
