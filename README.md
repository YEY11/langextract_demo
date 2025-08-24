# langextract_demo

一个使用 LangExtract（PyPI 版）通过 OpenAI 兼容服务进行结构化信息抽取的最小可运行示例（医疗场景，中文）。

场景示例为“胸痛就诊的心血管案例”，抽取要素包括：症状、体征、既往史、实验室检查、影像/心电图、诊断、用药/治疗、医嘱/随访。运行产物统一写入专门的输出目录，便于归档与对比。

本项目使用 loguru 替代 print 输出日志：
- 控制台彩色日志，级别可通过环境变量 LOG_LEVEL 控制（默认 INFO）
- 每次运行的日志同时写入 outputs/run-YYYYMMDD-HHMMSS/run.log，便于排查

此外，示例代码已显式指定使用 OpenAI Provider，因此可在 OpenAI 兼容网关下使用非 gpt-* 的模型名（例如 DeepSeek-V3.1、deepseek-chat），模型名将原样透传给你的网关。

## 环境要求
- Python 3.10+
- 建议使用 uv 管理依赖与虚拟环境：https://docs.astral.sh/uv/

## 安装依赖
在项目根目录执行：
```bash
uv sync
```
若你的环境未包含可选依赖，也可单独安装：
```bash
uv pip install "langextract[openai]" loguru python-dotenv
```

## 配置环境变量
1) 复制 .env.example 为 .env，并填写你的真实配置：
```bash
cp .env.example .env
```

2) .env 内容示例（按需修改为你的实际值）：
```bash
OPENAI_API_KEY="YOUR_LLM_API_KEY"
OPENAI_BASE_URL="YOUR_LLM_API_BASE_URL"   # 形如 https://your-endpoint/v1
LLM_MODEL_ID="YOUR_LLM_MODEL_ID"          # 例如 gpt-4o-mini 或 DeepSeek-V3.1
# 可选项
# OUTPUT_DIR="outputs"                     # 运行产物根目录（默认 outputs）
# LOG_LEVEL="INFO"                         # 日志级别：DEBUG/INFO/WARNING/ERROR
```

3) main.py 会自动加载 .env，并在启动时打印当前读取到的 Base URL、脱敏后的 API Key 与模型名，便于确认配置是否生效。

## 运行
```bash
uv run python main.py
```

## 切换模型（含 DeepSeek 等非 gpt-*）
- 使用 OpenAI 兼容网关（如 aihubmix、自建网关或厂商官方兼容接口）时，可直接设置 LLM_MODEL_ID 为该服务支持的模型名：
```bash
export OPENAI_BASE_URL="https://your-endpoint/v1"
export OPENAI_API_KEY="sk-xxx"
export LLM_MODEL_ID="DeepSeek-V3.1"       # 或 deepseek-chat、deepseek-reasoner 等
uv run python main.py
```
- 示例代码中通过 ModelConfig 显式指定 OpenAI Provider，避免因模型名不匹配导致的 Provider 解析失败。前提是你的服务真实兼容 OpenAI 协议，并支持该模型名。

## 结果与输出目录
- 程序会创建时间戳运行目录：outputs/run-YYYYMMDD-HHMMSS
- 写入文件包括：
  - extraction_results.jsonl：抽取后的标注结果（可用于二次处理/比对）
  - visualization.html：可视化页面（浏览器打开查看）
  - run.log：本次运行的完整日志

自定义输出根目录：
```bash
OUTPUT_DIR="runs" uv run python main.py
```
结果将写入 runs/run-YYYYMMDD-HHMMSS。

## 关键说明与注意事项
- 显式 OpenAI Provider：示例通过 LangExtract 的 ModelConfig 指定 OpenAI Provider，使你能以任意模型名（例如 DeepSeek-V3.1）在 OpenAI 兼容服务上调用。
- 不要在代码里传 base_url 参数：当前 PyPI 版本（如 1.0.x）不支持在 `lx.extract` 中直接传 base_url，请使用环境变量 OPENAI_BASE_URL 或 OPENAI_API_BASE。
- 模型名与网关一致：LLM_MODEL_ID 会原样传给你的网关，请确认网关实际支持该模型名。
- 依赖项：若报缺少 openai 包相关错误，请安装 `langextract[openai]` 可选依赖。

## 常见问题排查
- No provider registered for model_id='...'
  - 本示例已在代码中强制使用 OpenAI Provider。若仍出现，请确认你已更新到当前 main.py，并确保 OPENAI_BASE_URL 指向兼容 /v1 的网关且模型名受支持。
- TypeError: extract() got an unexpected keyword argument 'base_url'
  - 移除代码中的 base_url 参数，改用环境变量 OPENAI_BASE_URL/OPENAI_API_BASE。
- InferenceConfigError: OpenAI provider requires openai package
  - 安装可选依赖：`uv pip install "langextract[openai]"`
- ValueError: No provider registered for model_id='...'
  - 若你未使用本示例的强制 Provider 代码，请切换到 gpt-* 模型名，或更新 main.py 的显式 Provider 实现。
- .env 未生效
  - 检查启动日志是否打印了正确的 Base URL、模型名与脱敏后的 Key；
  - 或在 shell 中临时导出变量后再运行：
    ```bash
    export OPENAI_API_KEY=...
    export OPENAI_BASE_URL=https://your-endpoint/v1
    export LLM_MODEL_ID=gpt-4o-mini
    uv run python main.py
    ```
- 401/403
  - 检查 API Key、网关授权策略及是否需要额外的自定义 Header。

## 目录与文件提示
- main.py：医疗场景的中文示例脚本，包含 loguru 日志、显式 OpenAI Provider 与输出目录管理
- .env.example：环境变量示例文件（复制为 .env 并填写）
- outputs/：运行产物目录（已在 .gitignore 中忽略）
- extraction_results.jsonl、visualization.html、run.log 将生成在每次运行的时间戳子目录下

## 结果示例
- 抽取结果：
```json
{"extractions": [{"extraction_class": "症状", "extraction_text": "胸痛伴出汗2小时", "char_interval": null, "alignment_status": null, "extraction_index": 1, "group_index": 0, "description": null, "attributes": {"时间": "今晨", "性质": "突发", "持续时间": "2小时", "变化": "休息不缓解"}}, {"extraction_class": "既往史", "extraction_text": "2型糖尿病10年", "char_interval": {"start_pos": 11, "end_pos": 18}, "alignment_status": "match_lesser", "extraction_index": 2, "group_index": 1, "description": null, "attributes": {"疾病": "2型糖尿病", "病史": "10年"}}, {"extraction_class": "既往史", "extraction_text": "吸烟30年", "char_interval": null, "alignment_status": null, "extraction_index": 3, "group_index": 2, "description": null, "attributes": {"不良嗜好": "吸烟", "时间": "30年"}}, {"extraction_class": "体征", "extraction_text": "BP 150/95 mmHg", "char_interval": {"start_pos": 48, "end_pos": 62}, "alignment_status": "match_exact", "extraction_index": 4, "group_index": 3, "description": null, "attributes": {"收缩压": "150", "舒张压": "95", "单位": "mmHg"}}, {"extraction_class": "影像/心电图", "extraction_text": "II、III、aVF导联ST段抬高0.2mV", "char_interval": {"start_pos": 67, "end_pos": 89}, "alignment_status": "match_exact", "extraction_index": 5, "group_index": 4, "description": null, "attributes": {"导联": "II、III、aVF", "方向": "抬高", "幅度": "0.2mV"}}, {"extraction_class": "实验室检查", "extraction_text": "肌钙蛋白I 0.12 ng/mL", "char_interval": {"start_pos": 89, "end_pos": 110}, "alignment_status": "match_fuzzy", "extraction_index": 6, "group_index": 5, "description": null, "attributes": {"项目": "肌钙蛋白I", "数值": "0.12", "单位": "ng/mL", "结论": "升高"}}, {"extraction_class": "诊断", "extraction_text": "急性下壁心肌梗死", "char_interval": null, "alignment_status": null, "extraction_index": 7, "group_index": 6, "description": null, "attributes": {"性质": "初步诊断"}}, {"extraction_class": "用药/治疗", "extraction_text": "阿司匹林300mg嚼服", "char_interval": null, "alignment_status": null, "extraction_index": 8, "group_index": 7, "description": null, "attributes": {"药物": "阿司匹林", "剂量": "300mg", "途径": "嚼服"}}, {"extraction_class": "用药/治疗", "extraction_text": "替格瑞洛180mg负荷", "char_interval": null, "alignment_status": null, "extraction_index": 9, "group_index": 8, "description": null, "attributes": {"药物": "替格瑞洛", "剂量": "180mg", "途径": "负荷"}}, {"extraction_class": "用药/治疗", "extraction_text": "硝酸甘油静脉泵入", "char_interval": null, "alignment_status": null, "extraction_index": 10, "group_index": 9, "description": null, "attributes": {"药物": "硝酸甘油", "途径": "静脉泵入"}}, {"extraction_class": "用药/治疗", "extraction_text": "尽快行急诊PCI评估", "char_interval": null, "alignment_status": null, "extraction_index": 11, "group_index": 10, "description": null, "attributes": {"治疗": "急诊PCI评估", "时机": "尽快"}}], "text": "患者，男，58岁，既往2型糖尿病10年，吸烟30年。今晨突发胸痛伴出汗2小时，休息不缓解。查体：BP 150/95 mmHg。心电图：II、III、aVF导联ST段抬高0.2mV。实验室：肌钙蛋白I 0.12 ng/mL（升高）。初步诊断急性下壁心肌梗死。给予阿司匹林300mg嚼服、替格瑞洛180mg负荷、硝酸甘油静脉泵入，并尽快行急诊PCI评估。", "document_id": "doc_b9157900"}
```

- 可视化结果：
<img src="http://andy-blog.oss-cn-beijing.aliyuncs.com/2025-08-24-%E5%8F%AF%E8%A7%86%E5%8C%96%E7%BB%93%E6%9E%9C.png" alt="可视化结果">

## 新场景如何配置（快速适配指南）

当你需要将本示例适配到新的业务场景（例如急性脑卒中、感染科发热就诊、肿瘤随访等），按以下步骤操作。

**步骤 1：定义标签清单**
- 列出你希望抽取的“类别”清单（即 extraction_class），并明确每类常见属性。
- 示例（发热就诊场景，可按需增删）：
  - 症状：时间、持续时间、伴随症状、程度、诱因、缓解/加重因素
  - 体征：体温、脉搏、呼吸、血压、体格所见（部位、范围、程度）
  - 实验室检查：项目、数值、单位、参考范围、结论
  - 影像/检查：部位、所见、程度、分型/分期
  - 诊断：性质（初步/明确）、分型、分期
  - 用药/治疗：药物、剂量、频次、途径、时机
  - 医嘱/随访：时间、项目、频率

**步骤 2：修改提示词 prompt_description**
- 打开 main.py，更新 prompt 中的类别与“输出格式要求”。
- 保留以下硬性规则，能显著减少解析报错：
  - 抽取片段必须取自原文，禁止改写；
  - 不同实体片段不要重叠；
  - attributes 必须是对象（dict），不能是数组；
  - 同类多项必须拆成多条 extraction（如多种药物、多条检查）。

**步骤 3：准备少量 few-shot 示例（强烈建议）**
- 在 examples 中新增 1–2 个 ExampleData，让模型学习你的标签与属性粒度。
- 注意：
  - 使用关键字参数创建 Extraction（避免版本差异导致报错）：
    - extraction_class="类别名"
    - extraction_text="原文片段"
    - attributes={...} 或 None
  - 多药物/多检查要“拆开成多条”，每条的 attributes 为一个字典。

最小示例（粘贴到 main.py 的 examples 列表里，示例为“发热就诊”）
```python
lx.data.ExampleData(
    text="患者，男，30岁，发热2天，最高体温39.2℃，伴咳嗽、咽痛。体温38.8℃。血常规：白细胞12.3×10^9/L（升高）。给予对乙酰氨基酚0.5g口服，每6小时一次。",
    extractions=[
        lx.data.Extraction(
            extraction_class="症状",
            extraction_text="发热2天，最高体温39.2℃，伴咳嗽、咽痛",
            attributes={"持续时间": "2天", "最高体温": "39.2℃", "伴随症状": "咳嗽、咽痛"},
        ),
        lx.data.Extraction(
            extraction_class="体征",
            extraction_text="体温38.8℃",
            attributes={"体温": "38.8℃"},
        ),
        lx.data.Extraction(
            extraction_class="实验室检查",
            extraction_text="白细胞12.3×10^9/L（升高）",
            attributes={"项目": "白细胞", "数值": "12.3", "单位": "×10^9/L", "结论": "升高"},
        ),
        # 用药需拆成独立条目，attributes 必须是字典
        lx.data.Extraction(
            extraction_class="用药/治疗",
            extraction_text="对乙酰氨基酚0.5g口服，每6小时一次",
            attributes={"药物": "对乙酰氨基酚", "剂量": "0.5g", "途径": "口服", "频次": "q6h"},
        ),
    ],
)
```

**步骤 4：替换待抽取文本**
- 将 input_text 替换为你的新场景原始文本即可，也可批量改为文档列表。

**步骤 5：运行与验证**
```bash
uv run python main.py
```
- 结果会输出到 outputs/run-YYYYMMDD-HHMMSS/ 下的 JSONL 与 HTML。
- 若模型仍偶发将 attributes 生成为数组（list），可参考下方“可选增强（后处理兜底）”。

可选增强（强烈推荐）
1) 打开 schema 约束
   - 在 lx.extract 中设置 use_schema_constraints=True（本示例已开启）。
2) 增加一个“多项拆分”的 few-shot 示例
   - 专门示范把多个药物或检查拆分成多条 extraction。
3) 后处理兜底：将 attributes 为 list 的条目拆分成多条
   - 在调用 visualize/保存前，加一道轻量后处理，避免解析 ValueError：

```python
def split_list_attributes(result_doc):
    # 只示范单文档结果的最小处理；可按需扩展到批量
    fixed = []
    for item in result_doc.extractions:
        attrs = getattr(item, "attributes", None)
        if isinstance(attrs, list) and len(attrs) > 0 and all(isinstance(x, dict) for x in attrs):
            # 将一条合并的“同类多项”拆为多条
            for sub in attrs:
                fixed.append(
                    lx.data.Extraction(
                        extraction_class=item.extraction_class,
                        extraction_text=item.extraction_text,  # 或按需截取更精确的原文片段
                        attributes=sub,
                    )
                )
        else:
            fixed.append(item)
    result_doc.extractions = fixed
    return result_doc

# 使用示例：
result = lx.extract(...、use_schema_constraints=True、...)
result = split_list_attributes(result)
```

**常见坑位与建议**
- attributes 必须为字典：不要输出数组；同类多项请拆分为多条 extraction。
- 原文对齐：extraction_text 必须是原文片段，避免“意译/改写”，可提升对齐质量。
- 逐步迁移：先用 1–2 个短文本验证格式无误，再扩大到更复杂的临床记录。
- 模型与网关：新场景不影响网关配置，仍按项目“配置环境变量”章节设置即可。
