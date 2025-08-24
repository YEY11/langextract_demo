# 文件: main.py
import os
import sys
import textwrap
import datetime
import logging
import langextract as lx
from dotenv import load_dotenv
from loguru import logger

# 降低 absl 的日志噪声
logging.getLogger("absl").setLevel(logging.WARNING)

def mask_key(k: str | None, keep: int = 6) -> str:
    if not k:
        return "未设置"
    if len(k) <= keep:
        return "*" * len(k)
    return k[:keep] + "..." + "*" * 4

def setup_console_logger():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
    )
    return log_level

def add_file_logger(run_dir: str, log_level: str):
    log_path = os.path.join(run_dir, "run.log")
    logger.add(
        log_path,
        level=log_level,
        encoding="utf-8",
        enqueue=True,
        rotation="10 MB",
        retention="10 days",
        backtrace=True,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
    )
    logger.info(f"[日志] 文件日志已启用: {log_path}")

def build_model_config(model_id: str, api_key: str | None, base_url: str | None):
    # 显式指定使用 OpenAI Provider（字符串别名）。部分版本允许通过 provider_kwargs 传 key/base_url
    provider_kwargs = {}
    if api_key:
        provider_kwargs["api_key"] = api_key
    if base_url:
        provider_kwargs["base_url"] = base_url
    try:
        from langextract import factory as lxfactory
        cfg = lxfactory.ModelConfig(
            model_id=model_id,
            provider="openai",
            provider_kwargs=provider_kwargs or None,
        )
        logger.debug("[运行] 已使用 ModelConfig(provider='openai')")
        return cfg
    except Exception as e:
        logger.warning("[运行] 构建 ModelConfig(provider='openai') 失败，将回退默认 Provider：{}", e)
        return None

def main():
    # 0) 初始化控制台日志
    log_level = setup_console_logger()
    logger.info("[启动] 程序开始运行，日志级别: {}", log_level)

    # 1) 加载环境变量
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
    model_id = os.getenv("LLM_MODEL_ID", "gpt-4o-mini")
    logger.info("[环境] 已加载 .env")
    logger.info("[环境] OPENAI_BASE_URL/OPENAI_API_BASE = {}", base_url or "未设置")
    logger.info("[环境] OPENAI_API_KEY = {}", mask_key(api_key))
    logger.info("[环境] LLM_MODEL_ID = {}", model_id)

    # 2) 抽取任务与示例（强化输出规范）
    prompt = textwrap.dedent("""\
        从给定的临床文本中，按出现顺序抽取以下信息：
        1) 症状（主诉/伴随症状的原文片段）
        2) 体征（查体或生命体征的原文片段）
        3) 既往史（既往疾病/用药史的原文片段）
        4) 实验室检查（检验项目及数值的原文片段）
        5) 影像/心电图（影像或心电所见的原文片段）
        6) 诊断（明确或初步诊断的原文片段）
        7) 用药/治疗（药物/剂量/途径/时机等的原文片段）
        8) 医嘱/随访（复查/复诊等的原文片段）

        输出格式要求：
        - 输出 JSON 对象，键为 "extractions"，值为数组。
        - 数组的每个元素是一个对象，严格只包含两个键：
          a) "<类别名>"：对应原文片段（必须取自原文，不要改写）
          b) "<类别名>_attributes"：一个对象（字典），包含该片段的属性。
        - <类别名>_attributes 必须是对象（dict），不能是数组；没有属性时可省略或设为 null。
        - 如果同一类别有多条信息（例如多种药物），必须拆成多条独立的 extraction，而不是把多个属性放进数组。
          例：用药/治疗 同时有 3 种药物，则需输出 3 个独立的 "用药/治疗" 条目，每个条目的 attributes 是一个字典。

        一般属性示例（按需填写）：时间、部位、程度、数值、单位、参考范围、导联、用药剂量/频次/途径、时机等。
    """)

    # 示例 1：与你原来的类似
    examples = [
        lx.data.ExampleData(
            text=(
                "患者，女，45岁，因‘反复胸闷3月，加重1周’就诊。既往高血压病史5年，"
                "平素口服氨氯地平5mg qd。查体：BP 138/86 mmHg。心电图：V5–V6导联ST段压低0.1mV。"
                "实验室：肌钙蛋白I 0.02 ng/mL（未见升高）。急诊予硝酸甘油0.5mg含服，症状缓解。"
                "初步考虑‘稳定型心绞痛’，建议门诊随访复查心电图。"
            ),
            extractions=[
                lx.data.Extraction(
                    extraction_class="症状",
                    extraction_text="反复胸闷",
                    attributes={"持续时间": "3月", "近期变化": "加重1周"},
                ),
                lx.data.Extraction(
                    extraction_class="既往史",
                    extraction_text="高血压病史5年",
                    attributes={"用药": "氨氯地平5mg qd"},
                ),
                lx.data.Extraction(
                    extraction_class="体征",
                    extraction_text="BP 138/86 mmHg",
                    attributes={"收缩压": "138", "舒张压": "86", "单位": "mmHg"},
                ),
                lx.data.Extraction(
                    extraction_class="影像/心电图",
                    extraction_text="V5–V6导联ST段压低0.1mV",
                    attributes={"导联": "V5–V6", "方向": "压低", "幅度": "0.1mV"},
                ),
                lx.data.Extraction(
                    extraction_class="实验室检查",
                    extraction_text="肌钙蛋白I 0.02 ng/mL",
                    attributes={"项目": "肌钙蛋白I", "数值": "0.02", "单位": "ng/mL", "结论": "未升高"},
                ),
                lx.data.Extraction(
                    extraction_class="用药/治疗",
                    extraction_text="硝酸甘油0.5mg含服",
                    attributes={"药物": "硝酸甘油", "剂量": "0.5mg", "途径": "含服", "时机": "急诊"},
                ),
                lx.data.Extraction(
                    extraction_class="诊断",
                    extraction_text="稳定型心绞痛",
                    attributes={"性质": "初步考虑"},
                ),
                lx.data.Extraction(
                    extraction_class="医嘱/随访",
                    extraction_text="门诊随访复查心电图",
                    attributes={"时间": "门诊", "项目": "心电图"},
                ),
            ],
        ),
        # 示例 2：专门演示“多药物要拆成多条”
        lx.data.ExampleData(
            text="给予阿司匹林300mg嚼服、替格瑞洛180mg负荷、硝酸甘油静脉泵入。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="用药/治疗",
                    extraction_text="阿司匹林300mg嚼服",
                    attributes={"药物": "阿司匹林", "剂量": "300mg", "途径": "嚼服"},
                ),
                lx.data.Extraction(
                    extraction_class="用药/治疗",
                    extraction_text="替格瑞洛180mg负荷",
                    attributes={"药物": "替格瑞洛", "剂量": "180mg", "途径": "负荷"},
                ),
                lx.data.Extraction(
                    extraction_class="用药/治疗",
                    extraction_text="硝酸甘油静脉泵入",
                    attributes={"药物": "硝酸甘油", "途径": "静脉泵入"},
                ),
            ],
        ),
    ]

    # 待抽取的新文本
    input_text = (
        "患者，男，58岁，既往2型糖尿病10年，吸烟30年。今晨突发胸痛伴出汗2小时，休息不缓解。"
        "查体：BP 150/95 mmHg。心电图：II、III、aVF导联ST段抬高0.2mV。"
        "实验室：肌钙蛋白I 0.12 ng/mL（升高）。初步诊断急性下壁心肌梗死。"
        "给予阿司匹林300mg嚼服、替格瑞洛180mg负荷、硝酸甘油静脉泵入，并尽快行急诊PCI评估。"
    )

    # 3) 输出目录
    out_root = os.getenv("OUTPUT_DIR", "outputs")
    run_id = datetime.datetime.now().strftime("run-%Y%m%d-%H%M%S")
    run_dir = os.path.join(out_root, run_id)
    os.makedirs(run_dir, exist_ok=True)
    logger.info("[输出] 结果将写入目录: {}", run_dir)
    add_file_logger(run_dir, log_level)

    # 4) 执行抽取（显式使用 OpenAI Provider）
    logger.info("[运行] 即将调用 LangExtract.extract")
    logger.info("[运行] 使用模型: {}", model_id)
    logger.info("[运行] fence_output=True, use_schema_constraints=True")

    config = build_model_config(model_id, api_key, base_url)

    result = lx.extract(
        text_or_documents=input_text,
        prompt_description=prompt,
        examples=examples,
        fence_output=True,
        use_schema_constraints=True,  # 开启 schema 约束
        config=config,
    )

    # 5) 保存与可视化
    out_jsonl_name = "extraction_results.jsonl"
    out_html_name = "visualization.html"
    lx.io.save_annotated_documents([result], output_name=out_jsonl_name, output_dir=run_dir)

    jsonl_path = os.path.join(run_dir, out_jsonl_name)
    html_content = lx.visualize(jsonl_path)
    html_path = os.path.join(run_dir, out_html_name)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content.data if hasattr(html_content, "data") else html_content)

    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            line_count = sum(1 for _ in f)
    except Exception as e:
        logger.exception("[统计] 读取 {} 失败: {}", jsonl_path, e)
        line_count = "未知"

    logger.success("[完成] 已写入 {}（行数: {}）和 {}", jsonl_path, line_count, html_path)
    logger.info("[提示] 若结果为空或报错，请核对 OPENAI_BASE_URL 与 OPENAI_API_KEY 是否正确、以及你的服务是否兼容 OpenAI 接口。")

if __name__ == "__main__":
    main()
