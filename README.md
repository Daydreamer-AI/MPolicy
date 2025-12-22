# MPolicy

一个基于akshare、baostock的股票数据处理和技术分析工具，自带回放复盘功能。

## 效果图

## 功能特点

- 获取股票历史数据
- 计算技术指标（MACD、MA等）
- 数据存储和管理
- 自定义指标计算
- 自定义策略分析
- k线回放复盘

## 安装方法

首先克隆代码到本地仓库：

```bash
git clone ...
cd ...
```

### 创建虚拟环境

### 安装AKShare

AKShare 项目地址：https://github.com/akfamily/akshare

常规安装：

```bash
pip install akshare --upgrade
```

中国国内镜像安装：

```bash
pip install akshare -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com  --upgrade
```

验证：

```python
import akshare as ak

print(ak.__version__)
```

### 安装Baostock

Baostock 项目地址：https://pypi.org/project/baostock/

安装：

```bash
pip install baostock –upgrade
```

### 其他依赖安装

PyQt5 安装：

```bash
pip install PyQt5
```

## 使用示例

```bash
python main.py
```

## 文档

详细文档请参阅 [docs/](docs/) 目录。

## 贡献指南

欢迎提交问题和贡献代码，请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 更新SOP
日更：交易日18点后更新
1. Baostock--查询沪市主板股票、查询深市主板股票
2. AKShare--更新行业板块数据、更新每日筹码分布数据(废弃)
3. 策略筛选

周更：每周五收盘之后更新
1. Baostock--查询沪市主板股票、查询深市主板股票
2. AKShare--更新股票数据（流通值）


## 后续规划

1. 筛选条件设置。done。

2. 数据库接口多线程支持。done。

3. 补充A股行业、概念数据接口。通过AKShare接口实现。done。

4. 补充东方财富筹码分布数据接口。通过AKShare接口实现。done。

5. 补充行业板块、概念板块历史资金流。用于分析行业、概念板块主力净流入、超大单净流入、大单净流入、中单净流入、小单净流入、超小单净流入对其趋势行情的影响。done。

6. 提供个股历史资金流图表信息。用于分析个股主力净流入、超大单净流入、大单净流入、中单净流入、小单净流入、超小单净流入对股票涨跌幅的影响。无支持接口。

7. 添加股票数据可视化图表。done。

8. 添加自定义策略可视化图表。done。

9. 添加复盘UI交互，补充回放复盘功能。done。

10. 复盘回放优化。

11. 补充回放模拟交易。

12. 板块主图优化。

13. 数据获取优化。

14. 添加任务线程池。

15. UI及交互优化。
