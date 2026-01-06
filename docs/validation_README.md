# PredictLab 数据完整性和校验机制

## 📋 概述

PredictLab 数据完整性和校验机制提供从数据采集到最终分析的端到端质量保障。通过多层次校验、增量一致性保证和实时监控，确保数据的准确性、完整性和可靠性。

## 🏗️ 校验架构

### 三层校验体系

#### 🗃️ Raw Layer 校验
**校验内容**:
- 数据存在性检查
- 数据格式验证
- 必需字段完整性
- 时间戳有效性
- 数据哈希一致性

**校验规则示例**:
```python
# Raw数据存在性
if df.empty:
    raise ValidationError("Raw数据为空")

# 时间戳有效性
invalid_timestamps = df['timestamp'].isna().sum()
if invalid_timestamps > 0:
    log.warning(f"发现{invalid_timestamps}个无效时间戳")
```

#### 🧹 Clean Layer 校验
**校验内容**:
- 数据完整性 (缺失值检测)
- 数据唯一性 (重复数据检测)
- 时间序列连续性
- 数值合理性 (异常值检测)
- 业务逻辑一致性 (OHLC逻辑)

**校验规则示例**:
```python
# 缺失值检测
missing_values = df.isnull().sum()
if missing_values.any():
    log.warning(f"发现缺失值: {missing_values[missing_values > 0]}")

# OHLC逻辑校验
ohlc_valid = (
    (df['high'] >= df['open']) &
    (df['high'] >= df['close']) &
    (df['low'] <= df['open']) &
    (df['low'] <= df['close'])
)
invalid_count = (~ohlc_valid).sum()
```

#### 🎯 Feature Layer 校验
**校验内容**:
- 技术指标完整性
- 指标数值合理性
- 计算一致性验证
- 时间序列连续性

**校验规则示例**:
```python
# RSI范围校验
invalid_rsi = ((df['rsi_14'] < 0) | (df['rsi_14'] > 100)).sum()
if invalid_rsi > 0:
    log.error(f"RSI值超出合理范围: {invalid_rsi}条记录")

# 移动平均线合理性
ma_negative = (df['sma_20'] < 0).sum()
if ma_negative > 0:
    log.error(f"移动平均线出现负值: {ma_negative}条记录")
```

## ⚙️ 核心功能

### 数据校验器 (`data_validator.py`)

#### 主要方法
```python
# Raw数据校验
report = data_validator.validate_raw_data(data, source_type, ValidationLevel.STANDARD)

# Clean数据校验
report = data_validator.validate_clean_data(df, source_type, symbol, ValidationLevel.STRICT)

# Feature数据校验
report = data_validator.validate_feature_data(df, symbol, interval_type, ValidationLevel.STANDARD)

# 增量更新校验
report = data_validator.validate_incremental_update(existing_data, new_data, symbol, data_type)
```

#### 校验级别
- **BASIC**: 基础校验（存在性、格式）
- **STANDARD**: 标准校验（完整性、一致性）
- **STRICT**: 严格校验（业务规则、质量标准）
- **COMPREHENSIVE**: 全面校验（所有规则）

### 质量监控器 (`quality_monitor.py`)

#### 监控指标
```python
# Raw数据质量
"raw_completeness": "Raw数据完整性"
"raw_accuracy": "Raw数据准确性"
"raw_timeliness": "Raw数据及时性"

# Clean数据质量
"clean_completeness": "Clean数据完整性"
"clean_uniqueness": "Clean数据唯一性"
"clean_consistency": "Clean数据一致性"

# Feature数据质量
"feature_completeness": "Feature数据完整性"
"feature_accuracy": "Feature数据准确性"

# 系统级指标
"pipeline_success_rate": "管道成功率"
"data_freshness": "数据新鲜度"
```

#### 告警系统
```python
# 告警级别
alert.level in ["warning", "error", "critical"]

# 告警示例
QualityAlert(
    alert_id="raw_completeness_001",
    metric_id="raw_completeness",
    level="warning",
    message="Raw数据完整性低于阈值: 94.2% < 95.0%",
    details={"current_score": 94.2, "threshold": 95.0}
)
```

## 🔄 增量更新一致性保证

### 增量校验机制

#### 1. 数据冲突检测
```python
# 时间戳冲突检查
existing_times = set(existing_data['timestamp'])
new_times = set(new_data['timestamp'])
conflicts = existing_times & new_times

if conflicts:
    log.warning(f"发现{len(conflicts)}个时间戳冲突")
```

#### 2. 数据连续性验证
```python
# 检查增量更新后的时间连续性
combined_data = pd.concat([existing_data, new_data])
timestamps = combined_data['timestamp'].sort_values()
gaps = timestamps.diff().dropna()

# 检测异常间隔
median_gap = gaps.median()
abnormal_gaps = gaps > (median_gap * 5)
```

#### 3. 数值合理性检查
```python
# 增量数据与历史数据的数值分布比较
existing_prices = existing_data['price']
new_prices = new_data['price']

# Z-score异常检测
combined_prices = pd.concat([existing_prices, new_prices])
z_scores = (new_prices - combined_prices.mean()) / combined_prices.std()
outliers = (z_scores.abs() > 3).sum()
```

### 历史重算一致性

#### 版本控制
```python
# 指标重算版本管理
indicators_data['calculation_version'] = 'v1.2'
indicators_data['recalculation_timestamp'] = datetime.now()

# 历史版本比较
old_indicators = get_historical_indicators(symbol, interval, 'v1.1')
new_indicators = recalculate_indicators(symbol, interval)

# 差异分析
differences = compare_indicator_versions(old_indicators, new_indicators)
```

#### 数据隔离
```python
# 重算时使用数据快照
with transaction():
    # 创建临时表存储重算结果
    temp_table = create_temp_indicator_table()

    # 重算指标
    recalculated_data = perform_recalculation(base_data)

    # 校验重算结果
    validation_report = validate_recalculation_consistency(
        original_data, recalculated_data
    )

    if validation_report.is_pass:
        # 替换原数据
        replace_original_indicators(recalculated_data)
    else:
        # 回滚重算
        rollback_recalculation()
        log.error("重算结果校验失败，已回滚")
```

## 📊 报告和监控

### 校验报告格式

#### JSON报告
```json
{
  "data_type": "clean",
  "symbol": "BTC_PRICE",
  "validation_level": "standard",
  "total_records": 1000,
  "quality_score": 96.5,
  "is_pass": true,
  "issues": [
    {
      "rule_id": "clean_data_completeness",
      "level": "warning",
      "result": "warning",
      "message": "发现3个缺失值",
      "affected_records": 3
    }
  ]
}
```

#### HTML仪表板
```html
<!DOCTYPE html>
<html>
<head>
    <title>PredictLab 数据质量仪表板</title>
    <style>
        .metric { display: inline-block; margin: 10px; padding: 20px; border: 1px solid #ddd; }
        .alert { background: #ffebee; border-left: 4px solid #f44336; margin: 10px 0; padding: 10px; }
        .score { font-size: 24px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>PredictLab 数据质量仪表板</h1>
    <div class="metric">
        <h3>总体评分</h3>
        <div class="score">96.5</div>
    </div>
</body>
</html>
```

### 监控告警

#### 实时监控
```python
# 启动质量监控
await quality_monitor.start_monitoring(interval_minutes=60)

# 获取当前状态
active_alerts = quality_monitor.get_active_alerts()
current_metrics = await quality_monitor.run_quality_check()
```

#### 告警处理
```python
# 解决告警
quality_monitor.resolve_alert(alert_id)

# 获取告警历史
alert_history = quality_monitor.get_alert_history(days=7)
```

## 🔧 集成到数据管道

### 任务调度器集成

#### 校验任务示例
```python
# 在task_scheduler.py中添加校验任务

async def _task_validate_pipeline_step(self, step_name: str, symbol: str) -> Dict[str, Any]:
    """校验管道步骤的数据质量"""
    if step_name == "raw":
        # Raw数据校验
        data = await self._get_raw_data(symbol)
        report = data_validator.validate_raw_data(data, 'predict', ValidationLevel.STANDARD)

    elif step_name == "clean":
        # Clean数据校验
        data = await self._get_clean_data(symbol)
        report = data_validator.validate_clean_data(data, 'predict', symbol, ValidationLevel.STANDARD)

    elif step_name == "feature":
        # Feature数据校验
        data = await self._get_feature_data(symbol)
        report = data_validator.validate_feature_data(data, symbol, '1h', ValidationLevel.STANDARD)

    # 记录校验结果
    if not report.is_pass:
        log.warning(f"{step_name}数据校验未通过: {report.score:.1f}")
        # 可以选择继续或终止管道

    return {
        'step': step_name,
        'symbol': symbol,
        'score': report.score,
        'passed': report.is_pass,
        'issues': len(report.issues)
    }
```

### 数据管理器集成

#### 增量更新安全检查
```python
# 在data_manager.py中集成安全检查

async def safe_incremental_update(self, symbol: str, new_data: pd.DataFrame) -> bool:
    """安全增量更新"""
    # 1. 安全检查
    safety_check = await self.incremental_update_safety_check(symbol, new_data)

    if not safety_check['safe_to_update']:
        log.error(f"增量更新安全检查失败: {safety_check['errors']}")
        return False

    if safety_check['warnings']:
        log.warning(f"增量更新存在警告: {safety_check['warnings']}")

    # 2. 执行更新
    try:
        await self.perform_incremental_update(symbol, new_data)

        # 3. 后校验
        consistency_check = await self.validate_data_consistency(symbol)
        if not all(result.get('passed', False) for result in consistency_check.values()):
            log.error("增量更新后数据一致性校验失败")
            # 可以触发回滚
            return False

        log.info("增量更新成功且数据一致性校验通过")
        return True

    except Exception as e:
        log.error(f"增量更新失败: {e}")
        # 触发回滚
        await self.rollback_incremental_update(symbol)
        return False
```

## 📈 使用示例

### 命令行使用

#### 数据校验
```bash
# 校验所有数据层
python data_manager.py validate --symbol BTC_PRICE --data-type all

# 只校验Clean数据
python data_manager.py validate --symbol BTC_PRICE --data-type clean
```

#### 增量更新安全检查
```bash
# 检查增量更新安全性
python data_manager.py safety_check --symbol BTC_PRICE --data-type clean
```

#### 质量监控演示
```bash
# 运行质量监控演示
python quality_monitor_demo.py
```

### 编程接口

#### 基础校验
```python
from modules.validation.data_validator import data_validator, ValidationLevel

# 校验DataFrame
report = data_validator.validate_clean_data(df, 'predict', 'BTC_PRICE', ValidationLevel.STANDARD)

if report.is_pass:
    print(f"✅ 校验通过，质量评分: {report.score:.1f}")
else:
    print(f"❌ 校验失败，发现 {len(report.issues)} 个问题")

# 生成报告
html_report = data_validator.generate_validation_report(report, "html")
```

#### 质量监控
```python
from modules.validation.quality_monitor import quality_monitor

# 执行质量检查
report = await quality_monitor.run_quality_check(['raw', 'clean', 'feature'])

# 查看告警
active_alerts = quality_monitor.get_active_alerts()
for alert in active_alerts:
    print(f"🚨 {alert.level}: {alert.message}")

# 生成仪表板
dashboard_html = quality_monitor.generate_quality_dashboard()
```

#### 增量校验
```python
# 增量更新校验
validation_report = data_validator.validate_incremental_update(
    existing_data, new_data, 'BTC_PRICE', 'clean'
)

if validation_report.is_pass:
    print("✅ 增量更新安全")
    # 执行更新
else:
    print("❌ 增量更新存在风险")
    # 拒绝更新或执行修复
```

## 🎯 最佳实践

### 校验策略
1. **分层校验**: Raw→Clean→Feature逐步严格
2. **增量检查**: 新数据优先进行完整性校验
3. **定期重检**: 定期对历史数据进行重新校验
4. **告警响应**: 建立告警响应和处理流程

### 性能优化
1. **采样校验**: 对大数据集使用采样校验
2. **异步处理**: 校验任务异步执行不阻塞主流程
3. **缓存结果**: 缓存近期校验结果避免重复计算
4. **分批处理**: 大数据分批校验避免内存溢出

### 监控告警
1. **阈值设置**: 根据业务需求设置合理的质量阈值
2. **告警分级**: warning/error/critical 三级告警体系
3. **响应机制**: 建立自动响应和人工干预机制
4. **趋势分析**: 监控质量变化趋势，预测潜在问题

### 数据修复
1. **自动修复**: 对可自动修复的问题实施自动修复
2. **人工审核**: 复杂问题通过人工审核处理
3. **版本控制**: 修复操作记录版本便于回溯
4. **预防措施**: 基于校验结果改进数据采集流程

这个数据完整性和校验机制为PredictLab提供了企业级的**数据质量保障**，确保从数据源头到最终分析的**数据可信度**！ 🛡️✨
