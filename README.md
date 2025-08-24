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

如需扩展抽取要素（例如将“影像/心电图”拆分为“影像学”和“心电图”，或为“用药/治疗”补充频次/疗程等属性），或希望以命令行参数自定义输出目录、模型、提示词等，欢迎提出需求，我可以协助完善脚本。
