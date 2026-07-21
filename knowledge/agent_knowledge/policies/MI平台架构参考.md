# MI 平台架构参考（P3 - 仅作认知参考）

> 来源：`nexus/backend/boards/internal/service/report/handler/simple/`、`nexus/backend/assets/`
> 蒸馏日期：2026-06-20
> 层级：仅作 DataAgent 架构认知参考，不进入默认召回

## Simple 报表框架（Quick BI 集成）

MI 平台通过 `simple` handler 集成阿里云 Quick BI：

- 功能：配置化生成 Quick BI Ticket，嵌入 BI 报表到 MI 平台
- 端点：`/api/boards/simple/ticket-url`
- 权限：根据用户 username 自动生成 GlobalParam，实现数据权限隔离
- 用途：快速嵌入 Quick BI 看板到 MI，无需开发新报表

对 DataAgent 的意义：
- MI 中部分报表是 Quick BI 嵌入，非 nexus 自研
- Quick BI 报表的指标口径可能与 nexus 自研报表不一致，需区分数据来源

## Assets 素材管理服务

MI 平台的 Assets 服务管理创意素材的跨平台上传和分发：

### 支持的渠道

| 渠道 | 能力 |
|---|---|
| AppLovin | 上传素材、创建 Creative Set、获取上传结果 |
| TikTok | 上传视频/图片/Playable |
| XMP | 素材列表、素材上传、素材报告、素材文件夹 |
| UCloud | 对象存储（presign URL、上传） |

### 数据模型

- `assets`：素材主表
- `asset_jobs` / `asset_job_items`：素材上传任务
- `asset_projects`：素材项目
- `asset_tags` / `tag_categories`：标签体系
- `channel_assets`：渠道素材关联
- `designers`：设计师
- `languages`：语言

### 对 DataAgent 的意义

- Assets 服务是**操作层**，管理素材的上传和分发
- DataAgent 不需要直接交互 Assets 服务
- 但需要知道：`media_asset` 报表中的素材 ID 来源于这个系统
- 设计师归因数据通过 Assets 服务的 `designers` 表提供

## IAM 权限系统

MI 平台使用自建 IAM（Identity and Access Management）：

- SSO 登录（Verify Ticket → Sign In/Up）
- PBAC（Permission-Based Access Control）
- 部门/用户组/所有权管理
- 资源级权限（按 bundle_id 隔离数据）

对 DataAgent 的意义：
- MI 报表的数据范围受 IAM 权限控制
- 同一用户在不同产品（bundle_id）上可能有不同的数据可见范围
- Campaign 面板的"投放人员"筛选依赖 IAM ownership

## Boards 基础设施

### 看板模板系统

- `board_templates`：看板模板定义
- `board_template_shares`：模板分享
- `default_board_templates`：默认模板
- `board_benchmarks`：看板 benchmark 阈值

### 导出服务

- 支持 Excel 和 JSON 格式导出
- 异步队列处理（queue → tasker → worker）
- 大数据量导出走异步队列

### 预测服务集成

- 通过 `integration/forecast/` 对接外部预测服务
- ROI 预估段由预测服务补齐（蓝底标记）
- ROI Trend 通过 `integration/roi_trend/` 获取

### Excel 导入

- 支持 Excel 文件解析导入（`pkg/excelimport/`）
- 支持视频链接解析（`pkg/videolink/`）
