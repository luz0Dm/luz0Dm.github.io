#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cnec-eval-engine / evaluate.py
中文电商客服垂直评估执行引擎（单文件，纯 Python 标准库，PDF 可选 fpdf2）

功能：
  1. 读入评估集 JSONL（CNEC 格式：id/category/turns/user_input/expected_behavior/scoring_rubric）
  2. 逐题组装对话 → 调用被测模型（通用兼容对话接口，环境变量读 key）
  3. 用 judge 模型（与被测模型不同源）按 0-2 分 rubric 逐题评分
  4. 汇总 → 输出报告（PDF 优先，HTML 兜底）：总分表 / 分类得分 / 翻车案例 / 改进建议

依赖：
  - 必需：Python 3.8+ 标准库
  - 可选：fpdf2（pip install fpdf2）。未安装时自动降级输出 HTML 报告，不影响主流程。

环境变量（只从环境读 key，绝不写死在代码/配置文件里）：
  SUBJECT_API_KEY      被测模型 key（dry-run 模式不需要）
  SUBJECT_BASE_URL     被测模型接口地址，如 https://your-provider/v1
  SUBJECT_MODEL        被测模型名
  JUDGE_API_KEY        裁判模型 key（必须与被测模型不同源，避免自评偏差）
  JUDGE_BASE_URL       裁判模型接口地址
  JUDGE_MODEL          裁判模型名

用法：
  # 拿到两个 API key 后三步跑通（见 README.md）
  python evaluate.py --evalset evalset.jsonl --out ./report
  # 不真调 API，走完整流程输出模拟报告（用于验收/演示）
  python evaluate.py --evalset evalset.jsonl --out ./report --dry-run

参数：
  --evalset PATH     评估集 JSONL（必需）
  --out DIR          输出目录（默认 ./eval-report）
  --dry-run          模拟模式：不调 API，生成确定性的模拟回答与评分
  --limit N          只评估前 N 题（默认全部）
  --sample K         翻车案例最多收录 K 条（默认 10）
  --subject-name S   报告中被测方显示名（默认：SUBJECT_MODEL 或 "被测系统"）
  --watermark TEXT   报告水印（如 "DEMO 数据"）
  --title TEXT       报告标题
  --timeout SEC      单次 API 超时（默认 60）
  --max-retries N    单题重试次数（默认 2）
  --sleep SEC        每题间隔秒数（默认 0，可用来限速）
"""
import argparse
import datetime
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

VERSION = "1.0.0"

# ---------------------------------------------------------------- API 调用

def chat_completion(base_url, api_key, model, messages, timeout=60):
    """通用兼容对话接口（业界通行的 Chat Completions 协议）。只依赖标准库。"""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.0,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def build_subject_prompt(item):
    """把评估集条目组装成发给被测客服系统的消息序列。"""
    msgs = [{"role": "system",
             "content": "你是某电商店铺的客服助手，请基于对话上下文回答用户最新的问题。"}]
    for t in item.get("turns", []):
        r = t.get("role")
        if r in ("user", "assistant"):
            msgs.append({"role": r, "content": t.get("content", "")})
    msgs.append({"role": "user", "content": item["user_input"]})
    return msgs


def build_judge_prompt(item, subject_answer):
    """组装裁判评分 prompt。要求 judge 输出 JSON：{"score":0/1/2,"reason":"...","failure_type":"..."}"""
    rub = item["scoring_rubric"]
    lines = [
        "你是严格的中文电商客服质量评审员。请给下面的客服回答打分（0/1/2 整数分）。",
        "",
        "【用户问题】",
        item["user_input"],
        "",
        "【期望行为（评分基准）】",
        item["expected_behavior"],
        "",
        "【评分细则 rubric】",
        "2 分：" + rub.get("2", ""),
        "1 分：" + rub.get("1", ""),
        "0 分：" + rub.get("0", ""),
        "",
        "【被评客服的回答】",
        subject_answer,
        "",
        "只输出一个 JSON 对象，不要输出任何其他文字：",
        '{"score": 0或1或2, "reason": "一句中文评分理由（<=80字）", "failure_type": "若得分<2，用<=10个字概括主要翻车类型，如：编造参数/承诺过头/答非所问/规则解释错/工具调用缺失；得2分填空字符串"}',
    ]
    return [{"role": "user", "content": "\n".join(lines)}]


def parse_judge_output(text):
    """从 judge 输出中提取 JSON，容错处理包裹文字/代码块。"""
    if not text:
        return None
    m = re.search(r"\{[^{}]*\"score\"[^{}]*\}", text, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        score = int(obj.get("score", -1))
        if score not in (0, 1, 2):
            return None
        return {
            "score": score,
            "reason": str(obj.get("reason", ""))[:200],
            "failure_type": str(obj.get("failure_type", ""))[:50],
        }
    except (ValueError, TypeError):
        return None

# ---------------------------------------------------------------- dry-run 模拟

def _hash_int(seed_text, mod):
    return int(hashlib.md5(seed_text.encode("utf-8")).hexdigest(), 16) % mod


def dry_run_subject_answer(item):
    """确定性模拟被测回答：约 2/3 题答得还行，1/3 题翻车（编造/空话/答非所问）。"""
    kind = _hash_int("subject:" + item["id"], 10)
    if kind < 7:
        return ("您好，关于您的问题：「" + item["user_input"][:30] + "…」，"
                "这类情况我们一般按商品页公示规则处理，具体参数/库存/时效以页面与订单详情为准，"
                "如有出入我帮您核实并升级处理，请您放心。")
    if kind == 7:
        return "完全可以的，您放心拍就行，肯定没问题。"  # 承诺过头/答非所问
    if kind == 8:
        return "这个数值大概是行业标准的 3 倍左右，具体是 5.2 倍。"  # 编造具体数字
    return "亲亲，我们这边都很好的哦，销量第一呢。"  # 空话


def dry_run_judge(item, subject_answer):
    """确定性模拟裁判：空话/承诺过头→0；还行→1-2。"""
    if "完全可以" in subject_answer or "销量第一" in subject_answer:
        return {"score": 0, "reason": "空话/绝对承诺，未回应具体问题", "failure_type": "答非所问"}
    if "5.2 倍" in subject_answer:
        return {"score": 0, "reason": "编造具体倍数，违反 rubric 禁止编造数值", "failure_type": "编造参数"}
    return {"score": 1 + _hash_int("judge:" + item["id"], 2),
            "reason": "基本回应但缺少 rubric 要求的可核验细节",
            "failure_type": "细节缺失"}

# ---------------------------------------------------------------- 报告生成

def aggregate(results):
    total = len(results)
    scored = sum(r["judge"]["score"] for r in results)
    max_score = total * 2
    by_cat = {}
    for r in results:
        c = r["category"]
        by_cat.setdefault(c, {"n": 0, "score": 0, "fails": 0})
        by_cat[c]["n"] += 1
        by_cat[c]["score"] += r["judge"]["score"]
        if r["judge"]["score"] == 0:
            by_cat[c]["fails"] += 1
    dist = {0: 0, 1: 0, 2: 0}
    ftypes = {}
    for r in results:
        s = r["judge"]["score"]
        dist[s] += 1
        if s < 2:
            ft = r["judge"].get("failure_type") or "其他"
            ftypes[ft] = ftypes.get(ft, 0) + 1
    return {
        "total": total, "scored": scored, "max": max_score,
        "pct": round(100.0 * scored / max_score, 1) if max_score else 0.0,
        "by_cat": by_cat, "dist": dist, "failure_types": ftypes,
    }


FAILURE_ADVICE = {
    "编造参数": "对具体数值/参数回答设置『未知即说未知』的拒答护栏，并接商品知识库检索后再答。",
    "承诺过头": "禁用『保证/肯定/完全可以』类绝对承诺话术模板，改为『规则+兜底方案』表述。",
    "答非所问": "加强指代消解与多轮上下文拼接，对无法识别意图的问题触发澄清追问。",
    "规则解释错": "把促销/售后规则做成结构化知识卡，回答前强制检索命中条款再生成。",
    "工具调用缺失": "补订单/地址/物流工具调用链路，涉及改址、查单必须走工具而非凭记忆答。",
    "细节缺失": "按 rubric 做细粒度微调，重点补『可核验差异/机理/适用场景』类信息密度。",
}


def build_advice(agg, fails):
    tips = []
    for ft, cnt in sorted(agg["failure_types"].items(), key=lambda x: -x[1]):
        tips.append("%s（出现 %d 次）：%s" % (ft, cnt, FAILURE_ADVICE.get(ft, "建议人工复核该类型案例并补规则。")))
    if not tips:
        tips.append("本轮未发现明显翻车类型，建议扩大评估集难度或加入红队对抗题复测。")
    weak = sorted(agg["by_cat"].items(), key=lambda x: x[1]["score"] / max(1, x[1]["n"]))[:3]
    tips.append("优先补强分类：" + "、".join("%s（%.1f/2.0）" % (c, v["score"] / max(1, v["n"])) for c, v in weak))
    return tips


def _wrap_zh(text, width):
    """按字符宽度粗暴折行（中英文混排够用）。"""
    out, line = [], ""
    for ch in text:
        line += ch
        w = sum(2 if ord(c) > 127 else 1 for c in line)
        if w >= width or ch == "\n":
            out.append(line.rstrip("\n"))
            line = ""
    if line:
        out.append(line)
    return out


def render_pdf(path, meta, agg, fails, advice, font_path=None):
    from fpdf import FPDF  # 延迟导入，允许未安装时走 HTML

    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    font = "helvetica"
    if font_path and os.path.exists(font_path):
        pdf.add_font("zh", "", font_path)
        font = "zh"
    pdf.add_page()
    pdf.set_font(font, size=16)
    pdf.cell(0, 10, meta["title"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font, size=10)
    pdf.cell(0, 6, "生成时间: %s  |  被测方: %s  |  裁判: %s  |  模式: %s" % (
        meta["time"], meta["subject"], meta["judge"], meta["mode"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 水印
    if meta.get("watermark"):
        pdf.set_text_color(220, 220, 220)
        pdf.set_font(font, size=40)
        w = meta["watermark"]
        for i in range(4):
            pdf.text(20, 60 + i * 70, w)
        pdf.set_text_color(0, 0, 0)

    pdf.set_font(font, size=13)
    pdf.cell(0, 8, "一、总分", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font, size=11)
    pdf.cell(0, 7, "总得分 %d / %d（%.1f%%）| 题目数 %d | 满分率 %.1f%% | 零分率 %.1f%%" % (
        agg["scored"], agg["max"], agg["pct"], agg["total"],
        100.0 * agg["dist"][2] / max(1, agg["total"]),
        100.0 * agg["dist"][0] / max(1, agg["total"])), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font(font, size=13)
    pdf.cell(0, 8, "二、分类得分", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font, size=10)
    pdf.cell(60, 7, "分类", border=1)
    pdf.cell(25, 7, "题数", border=1)
    pdf.cell(30, 7, "均分(/2)", border=1)
    pdf.cell(25, 7, "零分题", border=1, new_x="LMARGIN", new_y="NEXT")
    for cat, v in sorted(agg["by_cat"].items()):
        pdf.cell(60, 7, cat, border=1)
        pdf.cell(25, 7, str(v["n"]), border=1)
        pdf.cell(30, 7, "%.2f" % (v["score"] / max(1, v["n"])), border=1)
        pdf.cell(25, 7, str(v["fails"]), border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font(font, size=13)
    pdf.cell(0, 8, "三、翻车案例（0-1 分题）", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font, size=9)
    if not fails:
        pdf.cell(0, 7, "无。", new_x="LMARGIN", new_y="NEXT")
    for r in fails:
        pdf.set_font(font, size=10)
        pdf.cell(0, 7, "[%s] %s | 得分 %d | %s" % (
            r["id"], r["category"], r["judge"]["score"], r["judge"].get("failure_type", "")),
            new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font, size=9)
        for label, key in (("用户", "user_input"), ("回答", "subject_answer"), ("裁判", None)):
            txt = r["judge"]["reason"] if key is None else r[key]
            for i, seg in enumerate(_wrap_zh(("%s: %s" % (label, txt))[:400], 90)):
                pdf.cell(0, 5, seg, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    pdf.ln(2)

    pdf.set_font(font, size=13)
    pdf.cell(0, 8, "四、改进建议", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font, size=10)
    for i, tip in enumerate(advice, 1):
        for seg in _wrap_zh("%d. %s" % (i, tip), 88):
            pdf.cell(0, 6, seg, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    pdf.output(path)


def render_html(path, meta, agg, fails, advice):
    e = html.escape
    rows = "".join(
        "<tr><td>%s</td><td>%d</td><td>%.2f</td><td>%d</td></tr>" % (
            e(cat), v["n"], v["score"] / max(1, v["n"]), v["fails"])
        for cat, v in sorted(agg["by_cat"].items()))
    cases = ""
    for r in fails:
        cases += ("<div class='case'><h3>[%s] %s — 得分 %d — %s</h3>"
                  "<p><b>用户：</b>%s</p><p><b>回答：</b>%s</p><p><b>裁判：</b>%s</p></div>" % (
                      e(r["id"]), e(r["category"]), r["judge"]["score"],
                      e(r["judge"].get("failure_type", "")),
                      e(r["user_input"]), e(r["subject_answer"]), e(r["judge"]["reason"])))
    tips = "".join("<li>%s</li>" % e(t) for t in advice)
    watermark = ("<div class='wm'>%s</div>" % e(meta["watermark"])) if meta.get("watermark") else ""
    doc = """<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>%(title)s</title><style>
body{font-family:-apple-system,'Microsoft YaHei',sans-serif;max-width:900px;margin:2em auto;padding:0 1em;color:#222}
.wm{position:fixed;top:40%%;left:20%%;font-size:5em;color:#eee;transform:rotate(-20deg);z-index:-1}
table{border-collapse:collapse;width:100%%}td,th{border:1px solid #999;padding:4px 8px}
.case{border:1px solid #ddd;border-radius:6px;padding:.6em 1em;margin:.8em 0;background:#fafafa}
h1{border-bottom:3px solid #333;padding-bottom:.2em}
</style></head><body>%(wm)s
<h1>%(title)s</h1>
<p>生成时间：%(time)s ｜ 被测方：%(subject)s ｜ 裁判：%(judge)s ｜ 模式：%(mode)s</p>
<h2>一、总分</h2>
<p><b>%(scored)d / %(max)d（%(pct).1f%%）</b>｜ 题目数 %(total)d ｜ 满分 %(d2)d 题 / 1 分 %(d1)d 题 / 0 分 %(d0)d 题</p>
<h2>二、分类得分</h2>
<table><tr><th>分类</th><th>题数</th><th>均分(/2)</th><th>零分题</th></tr>%(rows)s</table>
<h2>三、翻车案例</h2>%(cases)s
<h2>四、改进建议</h2><ol>%(tips)s</ol>
</body></html>""" % {
        "title": e(meta["title"]), "time": e(meta["time"]), "subject": e(meta["subject"]),
        "judge": e(meta["judge"]), "mode": e(meta["mode"]), "scored": agg["scored"],
        "max": agg["max"], "pct": agg["pct"], "total": agg["total"],
        "d2": agg["dist"][2], "d1": agg["dist"][1], "d0": agg["dist"][0],
        "rows": rows, "cases": cases or "<p>无。</p>", "tips": tips, "wm": watermark,
    }
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)

# ---------------------------------------------------------------- 主流程

def load_evalset(path, limit=None):
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    if limit:
        items = items[:limit]
    return items


def run(args):
    items = load_evalset(args.evalset, args.limit)
    print("[*] 评估集 %d 题 | 模式: %s" % (len(items), "DRY-RUN 模拟" if args.dry_run else "真实 API"), file=sys.stderr)

    subj_key = os.environ.get("SUBJECT_API_KEY", "")
    subj_url = os.environ.get("SUBJECT_BASE_URL", "")
    subj_model = os.environ.get("SUBJECT_MODEL", "")
    judge_key = os.environ.get("JUDGE_API_KEY", "")
    judge_url = os.environ.get("JUDGE_BASE_URL", "")
    judge_model = os.environ.get("JUDGE_MODEL", "")

    if not args.dry_run:
        missing = [n for n, v in (("SUBJECT_API_KEY", subj_key), ("SUBJECT_BASE_URL", subj_url),
                                  ("SUBJECT_MODEL", subj_model), ("JUDGE_API_KEY", judge_key),
                                  ("JUDGE_BASE_URL", judge_url), ("JUDGE_MODEL", judge_model)) if not v]
        if missing:
            print("[!] 缺少环境变量: %s（或用 --dry-run 先跑模拟流程）" % ",".join(missing), file=sys.stderr)
            sys.exit(2)

    results = []
    for i, item in enumerate(items, 1):
        sid = item["id"]
        if args.dry_run:
            answer = dry_run_subject_answer(item)
            judge = dry_run_judge(item, answer)
        else:
            answer = None
            for attempt in range(args.max_retries + 1):
                try:
                    answer = chat_completion(subj_url, subj_key, subj_model,
                                             build_subject_prompt(item), timeout=args.timeout)
                    break
                except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as ex:
                    print("[!] %s 被测调用失败(%d/%d): %s" % (sid, attempt + 1, args.max_retries + 1, ex), file=sys.stderr)
                    time.sleep(2 ** attempt)
            if answer is None:
                answer = "[被测系统无响应]"
            judge = None
            for attempt in range(args.max_retries + 1):
                try:
                    out = chat_completion(judge_url, judge_key, judge_model,
                                          build_judge_prompt(item, answer), timeout=args.timeout)
                    judge = parse_judge_output(out)
                    if judge is None:
                        raise ValueError("judge 输出无法解析")
                    break
                except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as ex:
                    print("[!] %s 裁判调用失败(%d/%d): %s" % (sid, attempt + 1, args.max_retries + 1, ex), file=sys.stderr)
                    time.sleep(2 ** attempt)
            if judge is None:
                judge = {"score": 0, "reason": "裁判模型解析失败，人工复核", "failure_type": "裁判异常"}
        results.append({
            "id": sid, "category": item["category"], "difficulty": item.get("difficulty", 0),
            "user_input": item["user_input"], "expected_behavior": item["expected_behavior"],
            "subject_answer": answer, "judge": judge,
        })
        print("[+] %s 得分 %d" % (sid, judge["score"]), file=sys.stderr)
        if args.sleep:
            time.sleep(args.sleep)

    agg = aggregate(results)
    fails = [r for r in results if r["judge"]["score"] < 2][:args.sample]
    advice = build_advice(agg, fails)
    meta = {
        "title": args.title or "中文电商客服垂直评估报告",
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "subject": args.subject_name or subj_model or "被测系统",
        "judge": judge_model or ("dry-run 模拟裁判" if args.dry_run else "未知裁判"),
        "mode": "DRY-RUN 模拟（未调用真实 API）" if args.dry_run else "真实 API",
        "watermark": args.watermark,
    }

    os.makedirs(args.out, exist_ok=True)
    # 原始结果 JSON（可复核、可二次分析）
    raw_path = os.path.join(args.out, "results.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "aggregate": agg, "results": results}, f, ensure_ascii=False, indent=2)

    # 报告：PDF 优先，HTML 兜底
    pdf_path = os.path.join(args.out, "report.pdf")
    html_path = os.path.join(args.out, "report.html")
    report_path = None
    try:
        font = None
        for cand in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                     os.path.expanduser("~/.local/share/fonts/wqy-microhei.ttc"),
                     "/usr/share/fonts/truetype/unifont/unifont.ttf"):
            if os.path.exists(cand):
                font = cand
                break
        render_pdf(pdf_path, meta, agg, fails, advice, font_path=font)
        report_path = pdf_path
    except ImportError:
        render_html(html_path, meta, agg, fails, advice)
        report_path = html_path
    # HTML 始终额外输出一份（便于浏览器查看/转发）
    if not os.path.exists(html_path):
        render_html(html_path, meta, agg, fails, advice)

    print("\n==== 评估完成 ====", file=sys.stderr)
    print("总得分 %d/%d（%.1f%%）| 零分题 %d | 报告: %s" % (
        agg["scored"], agg["max"], agg["pct"], agg["dist"][0], report_path), file=sys.stderr)
    print(json.dumps({"report": report_path, "html": html_path, "raw": raw_path,
                      "score_pct": agg["pct"]}, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description="中文电商客服垂直评估执行引擎")
    p.add_argument("--evalset", required=True, help="评估集 JSONL 路径")
    p.add_argument("--out", default="./eval-report", help="输出目录")
    p.add_argument("--dry-run", action="store_true", help="模拟模式：不调用真实 API")
    p.add_argument("--limit", type=int, default=0, help="只评估前 N 题")
    p.add_argument("--sample", type=int, default=10, help="翻车案例最多收录条数")
    p.add_argument("--subject-name", default="", help="报告中被测方显示名")
    p.add_argument("--watermark", default="", help="报告水印文字")
    p.add_argument("--title", default="", help="报告标题")
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--sleep", type=float, default=0.0)
    args = p.parse_args()
    run(args)


if __name__ == "__main__":
    main()
