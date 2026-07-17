"""
Agent 工具定义。
每个工具用 @tool 装饰器，LLM 根据描述自动选择调用。
"""
import math
from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """
    计算数学表达式。支持四则运算、幂运算、三角函数、对数等（通过 Python eval 执行）。
    输入示例: "2**10", "sqrt(16)+3*4", "sin(pi/2)"
    返回数值字符串。
    """
    # 安全白名单：只允许数学相关函数和运算符
    allowed_names = {
        "abs", "round", "max", "min", "sum",
        "int", "float", "str", "len",
        "pi", "e", "tau", "inf", "nan",
        "sqrt", "pow", "log", "log10", "log2", "exp",
        "sin", "cos", "tan", "asin", "acos", "atan",
        "sinh", "cosh", "tanh",
        "degrees", "radians",
        "ceil", "floor", "trunc",
    }
    # 只允许安全的内置函数 + math 函数
    safe_dict = {name: getattr(math, name) for name in dir(math) if name in allowed_names}
    safe_dict.update({"abs": abs, "round": round, "max": max, "min": min, "sum": sum,
                      "int": int, "float": float, "str": str, "len": len})
    try:
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def get_current_weather(city: str) -> str:
    """
    查询指定城市的实时天气。
    city: 城市名称，如 "北京"、"上海"、"杭州"。
    返回天气概况（模拟数据，实际生产可接API）。
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴，温度32°C，湿度45%，风力3-4级",
        "上海": "多云转阴，温度29°C，湿度65%，风力2-3级，可能有阵雨",
        "广州": "雷阵雨，温度34°C，湿度80%，风力3-4级",
        "深圳": "晴间多云，温度33°C，湿度60%，风力2级",
        "杭州": "小雨转多云，温度27°C，湿度70%，风力1-2级",
        "成都": "阴天，温度25°C，湿度75%，微风",
        "武汉": "晴转多云，温度31°C，湿度55%，风力2-3级",
        "南京": "多云，温度30°C，湿度50%，风力2级",
        "西安": "晴，温度35°C，湿度30%，微风",
    }
    if city in weather_data:
        return f"{city}天气：{weather_data[city]}"
    return f"暂无{city}的天气数据。已知城市：{', '.join(weather_data.keys())}"


@tool
def query_knowledge_base(question: str) -> str:
    """
    从知识库中检索信息（模拟）。
    可用于查询企业规章制度、操作手册、FAQ 等信息。
    """
    knowledge = {
        "报销流程": "提交发票 → 部门主管审批 → 财务审核 → 3个工作日内打款",
        "年假政策": "入职满1年享5天年假，满3年享10天，满5年享15天。每年1月1日重置。",
        "VPN使用": "下载公司VPN客户端 → 用企业邮箱账号登录 → 选择对应线路即可连接",
        "打印机IP": "研发区打印机IP: 192.168.1.100，行政区打印机IP: 192.168.1.101",
        "会议室预订": "登录OA系统 → 资源管理 → 会议室预订 → 选择时间及会议室",
    }
    for key, answer in knowledge.items():
        if key in question:
            return answer
    return f"在知识库中未找到关于「{question}」的相关信息。"


# 工具列表：LLM 可用工具的全集
TOOLS = [
    calculator,
    get_current_weather,
    query_knowledge_base,
]