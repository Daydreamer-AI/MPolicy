# MPolicy

一个基于akshare、baostock的股票数据处理和技术分析工具。

## 效果图

## 功能特点

- 获取股票历史数据
- 计算技术指标（MACD、MA等）
- 数据存储和管理
- 自定义指标计算
- 自定义策略分析

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



## 后续规划

1. 筛选条件设置。或者直接动态修改筛选逻辑？

2. 数据库接口多线程支持

3. 补充A股行业、概念数据接口。通过AKShare接口实现。