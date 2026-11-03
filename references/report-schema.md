# 报告数据协议

使用 UTF-8 JSON。运行 `scripts/report_model.py` 中的 `load_report()` 校验后再渲染。

## 业务模式与铺量数据

普通账号沿用既有 JSON。用户明确选择素人帖铺量时，设置 `seeding_mode: true`，通过同一组读取、渲染和检查脚本生成铺量方案。

| 字段 | 填写方式 |
| --- | --- |
| `client_company_name`, `platform`, `generated_date` | 客户名、投放平台和报告日期。 |
| `goal`, `target_audience`, `target_volume` | 投放目标、核心人群和可选的计划篇数。 |
| `seeding_directions` | 至少15个不同方向。每项填 `name`、`audience_or_scene`、`angle`、`titles`。有明确分配时再填 `allocated_posts`。 |
| `seeding_examples` | 用户提供的原帖截图。每项填本地原图路径 `screenshot` 和可借鉴点 `takeaway`，从1编号。已知来源时填 `source_platform`。用于抖音项目的小红书截图仍注明来自小红书。 |
| `derived_topics` | 针对本批示例另拟3–5题。每条填 `title`、针对本品牌的新角度 `angle`、对应示例编号 `example_numbers`。 |
| `brand_support` | 最多3项品牌号配合动作，每项最多120字，说明如何承接搜索、咨询、购买或到店。 |
| `seeding_review_complete` | 用户选定方向、拟题及截图延展题，且原帖资料已处理时标记为true。 |
| `benchmarks`, `benchmark_review_complete` | 沿用已确认对标账号的资料与评审约定。单篇素人示例另存。 |

尚未开设品牌号时，可凭投放简报、帖子示例和已确认的对标资料完成铺量方案。主页链接、粉丝量、四维诊断、内容支柱与品牌号选题属于下面的常规模式。

## 常规账号方案顶层字段

- 身份：`client_company_name`、`platform`、`account_name`、`account_url`。
- 账号主体：必填 `account_subject`，值为 `person` 或 `brand`。个人 IP 使用 `person`；饭店、企业、品牌等非个人主体使用 `brand`，不根据是否有人出镜替代主体判断。
- 主页资料：`account_name` 保留来源原文；`account_bio` 为最多500字符的字符串，默认“暂未获取”。`profile_screenshot` 为可选本地主页原图路径，默认 `null`；`profile_screenshot_note` 为最多120字符的说明，默认空字符串。缺少完整主页时，说明中明确标注局部截图，不能推测缺失数据。
- 日期：`generated_date`、`data_date`，格式 `YYYY-MM-DD`。
- 摘要：`stage`、`summary`、`opportunity`。
- 现有内容类型：`current_content_types` 为最多6项字符串列表，默认空列表；只简短归纳已核验的内容类型。
- 数据：`metrics` 固定为粉丝量、获赞与收藏、更新频率、近期平均互动、最高互动内容、数据截取日期；缺失值校验后变为“暂未获取”，截取日期始终取 `data_date`。
- 分析：`diagnoses` 恰好包含定位、内容、表达、转化；`evidence_type` 为 `fact`、`inference` 或 `unknown`。
- 问题与优化动作：`problems` 为 3-5 项，每项包含问题、依据、影响、建议和优先级，按建议执行顺序填写。每项的执行先后序号和优先级在表内显示。
- 策略：`positioning` 最多180字符，个人 IP 填真实核心印象总句，非个人主体填账号定位句；另有 `target_audience`、`follow_reason`，以及可选字符串 `slogan`（最多40字符）、`content_style`（最多80字符）。品牌定位概括品类价值、地域或场景、目标人群、真实可支持的差异标签与要建立的核心印象。
- 个人 IP 四问：`ip_profile` 为可选结构，含 `identity`、`audience`、`value`、`expression` 四个非空字符串，每项1-120字符，分别回答“我是谁、我帮谁、我分享什么、我怎么表达”。`account_subject: person` 时必须填写；`brand` 不使用。这里描述真实身份、服务人群、分享价值和表达特征，不能填写出镜安排或拍摄动作来代替人设。
- 账号目标：`goal` 为1-12字符的字符串，默认“关注”，按实际业务目标填写，用于呈现关注、种草、购买或到店理由。
- 历史兼容：`persona`（最多80字符）、`persona_suggestions`（最多5项字符串列表，默认空列表）、`persona_purpose`（最多120字符，默认空字符串）仅兼容历史输入，新版不渲染这些旧字段或旧动作列表。执行建议填写优化动作或内容呈现形式。
- 优化与承接：`optimization_logic` 为最多3项字符串的顺序列表；`conversion_path` 最多5项；`production_loop` 最多6项。三者默认空列表，每项最多36字符，按实际顺序描述步骤。
- 第六模块标题：可选 `closing_section_title`，省略时默认“落地路径”。仅填写文字部分，不带编号，例如“到店承接”或“制作与复盘”；渲染时自动添加“六、”。前五个模块标题固定，不开放 JSON 改名或调整顺序。
- 内容：`pillars` 默认为三个，允许 3-5 个，占比合计 100。每项的 `purpose`（最多60字符）说明用户需求或业务任务，`format`（最多40字符）说明推荐呈现方式，`columns` 为代表栏目。
- 对标评审状态由 `benchmark_review_complete` 表示，默认 `false`。真实成稿须为 `true`，表示已在当前聊天确认最终名单、处理入选账号资料并完成逐项分析。研究中的候选清单不作为成稿数据。初选通常3–5个，`benchmarks` 只含最终入选账号，数量以用户明确确认的名单为准。同赛道、同阶段或形式参考按实际选择，不要求覆盖全部类型。
- 品牌客户和铺量项目的最终入选账号须填 `account_kind: "brand"` 和可追溯的 `brand_identity_evidence`，例如品牌官网链接指向同一账号ID。历史资料缺省为 `unknown`，需补核身份。素人、达人等个人创作者填 `creator`，其作品可作为铺量帖示例。
- 真实成稿的每个 `benchmarks` 项须与项目同平台，并满足 `user_confirmed: true` 和 `verified: true`。`name` 填精确账号名。`screenshot` 填入选账号的主页原图本地路径。`recent_performance` 写近期表现的时间范围、样本与可见指标。`content_analysis` 以代表作品或内容观察为依据。`reason`、`learn`、`avoid` 分别写推荐理由、可执行的借鉴点、不宜照搬的部分。`source_note` 留存内部核验说明。
- 用户明确接受某个材料缺口时，记录接受的具体范围，分析字段写已有样本能支持的判断及限制，缺图不造路径，缺数不造指标。只要名单未定、入选账号尚未核实、仍在等待补充资料或分析未完成，就不能将评审标记为完成并生成最终PDF或文字。
- 选题：3-5项互不重复的 `topic_directions`（每项1-20字符）、`trend_note` 和15-30个 `topics`。每条 `direction` 必须引用已声明的方向，渲染时以紧凑表格按方向组织；方向应与内容支柱对应，不增加脚本字段。
- 图片：`screenshots` 最多五个本地文件路径，仅作内部分析证据，不逐张展示；从资料中确认一张主页图后设置 `profile_screenshot`，只展示该图，不按列表顺序猜测。“三、内容方向参考”不显示截图；对标截图由对应 `benchmarks` 项提供。
- 演示：`sample_mode` 默认为 `false`。仅明确的模板演示可设为 `true` 并使用未核验示例对标；实际客户报告必须保持 `false` 并完成核验。

## 常规账号方案的模块顺序与页面安排

1. **一、账号诊断**：依次为来源原文账号昵称、用户主页原图及必要的局部说明、基于粉丝/获赞收藏/简介直接证据的当前阶段、简短现有内容类型、定位/内容/表达/转化四维问题表格、本次方案核心方向。首页保留客户品牌名和方案名。
2. **二、定位优化**：首项正文标题编号1，`person` 显示“账号人设（IP定位）”，包括核心印象总句与四问；`brand` 显示“账号定位”，呈现定位句。之后保留三字段表格：目标用户、与目标对应的关注/种草/购买/到店理由、打造账号记忆点，字段不加序号。按需显示“2、优化逻辑”。动作表上方的小标题为“优化动作”，无编号、无后缀。表内保留3-5项动作及独立的执行先后序号和优先级。
3. **三、内容方向参考**：保留文字方向、配比、任务、栏目与形式，使用表格，表内方向行标题不加序号，不放截图。
4. **四、选题建议**：按方向组织的15-30个选题，使用紧凑表格，热点融入对应方向。
5. **五、对标账号参考**：根据用户最终确认的名单，逐个展示已核实的账号、主页截图、近期表现、内容分析、推荐理由、借鉴点及不宜照搬的部分，内部保留核验记录。
6. 已有业务承接或制作复盘步骤时增加模块，标题由“六、”加 `closing_section_title` 组成，默认 **六、落地路径**；可按内容命名为 **六、到店承接** 或 **六、制作与复盘**。

前五个模块标题与顺序固定。各模块仅显示一个15pt绿色标题，不额外叠加黑色页面标题，正文11pt；首页的客户品牌名30pt和方案名22pt属于整份报告名称，予以保留。连续紧凑排版，模块可跨页，同页可有多个模块，表格优先，标题与后续内容保持在一起。续页如重复标题，保持原文，不附加“续”，由页脚页码区分。不强制一模块一页，不为达到5-7页补内容或拉开间距，也不缩小正文来压页数。

PDF和飞书文字中的“优化动作”小标题相同。其他正文二级标题在各模块内从1连续编号，跨页不重置。表格字段和行标题无序号，不占正文标题序号。选题序号、执行先后等独立序号列保持。

## 文本长度建议

- 客户公司名与账号名：不超过 40 个汉字。
- 摘要、机会：不超过 100 个汉字。
- 定位或个人核心印象总句：不超过180字符。
- 诊断和问题字段：每项 20-60 个汉字。
- 对标的推荐理由、可借鉴点、不宜照搬之处各建议15–45字。`recent_performance` 和 `content_analysis` 各最多240字符。`source_note` 最多120字符。
- 选题标题：不超过 40 个汉字。

如默认字体不可用，设置环境变量 `MOMENTUM_PDF_FONT` 指向可读取的中文 TTF/TTC 字体。

## 运行示例

依赖 Python 3.10+、Pydantic 2、ReportLab、Pillow、pypdf，以及用于预览的 Poppler `pdftoppm`。优先使用当前环境已有依赖。

在 Skill 文件夹中运行：

```bash
python3 scripts/render_report.py assets/sample-report.json sample.pdf
python3 scripts/validate_output.py assets/sample-report.json sample.pdf previews
```

`assets/sample-report.json` 为虚构的版式演示。制作客户报告时另存为项目 JSON，替换为已核实的账号资料，设置 `sample_mode: false`，截图使用本地绝对路径，按 [对标研究流程](intake-and-research.md) 确认并分析对标名单，再核验热点。

