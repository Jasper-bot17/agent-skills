#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
API 测试生成脚本

功能：
- 从 JSON 描述文件生成 API 测试套件
- 支持 curl 命令、Python unittest、Postman 集合三种输出格式
- 支持 GET/POST/PUT/DELETE/PATCH
- 支持 Bearer Token 认证、请求头、查询参数、请求体
- 自动生成状态码验证、JSON 字段检查
- 可直接执行测试并生成 HTML/Markdown 报告
- 纯 Python 标准库，无外部依赖

用法：
  python3 generate_api_tests.py --input api.json --format python
  python3 generate_api_tests.py --input api.json --format all --output tests/
  python3 generate_api_tests.py --input api.json --format python --run --report
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import html as html_mod


# ============================================================
# API 描述加载与校验
# ============================================================

def load_api_description(filepath):
    """加载并校验 API 描述文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        desc = json.load(f)

    if "base_url" not in desc:
        raise ValueError("API 描述文件缺少 base_url 字段")
    if "endpoints" not in desc or not isinstance(desc["endpoints"], list):
        raise ValueError("API 描述文件缺少 endpoints 数组")

    # 补全默认值
    desc.setdefault("auth", {"type": "none"})
    desc.setdefault("default_headers", {})
    desc.setdefault("name", "API Test Suite")

    for i, ep in enumerate(desc["endpoints"]):
        if "method" not in ep or "path" not in ep:
            raise ValueError(f"端点 {i} 缺少 method 或 path 字段")
        ep.setdefault("name", f"{ep['method']} {ep['path']}")
        ep.setdefault("headers", {})
        ep.setdefault("params", {})
        ep.setdefault("body", None)
        ep.setdefault("expect_status", 200)
        ep.setdefault("expect_fields", [])
        ep.setdefault("max_response_time", None)

    return desc


# ============================================================
# curl 命令生成
# ============================================================

def generate_curl(desc, output_dir):
    """生成 curl 命令脚本"""
    lines = []
    lines.append("#!/bin/bash")
    lines.append(f"# API 测试 - curl 命令集合")
    lines.append(f"# 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f'BASE_URL="{desc["base_url"]}"')

    auth = desc.get("auth", {})
    if auth.get("type") == "bearer":
        lines.append(f'TOKEN="{auth.get("token", "")}"')
        lines.append('AUTH_HEADER="Authorization: Bearer $TOKEN"')
    elif auth.get("type") == "apikey":
        lines.append(f'API_KEY="{auth.get("key", "")}"')
        lines.append(f'AUTH_HEADER="{auth.get("header", "X-API-Key")}: $API_KEY"')
    else:
        lines.append('AUTH_HEADER=""')

    lines.append("")

    for i, ep in enumerate(desc["endpoints"], 1):
        method = ep["method"].upper()
        path = ep["path"]
        name = ep.get("name", f"{method} {path}")

        lines.append(f'echo "=== {i}. {name} ==="')

        # 构建 URL（含查询参数）
        url = f'"$BASE_URL{path}"'
        if ep.get("params"):
            query = urllib.parse.urlencode(ep["params"])
            url = f'"$BASE_URL{path}?{query}"'

        # 构建 curl 命令
        cmd_parts = [f"curl -s -X {method}", url]

        # 认证头
        if auth.get("type") in ("bearer", "apikey"):
            cmd_parts.append('-H "$AUTH_HEADER"')

        # 默认请求头
        for k, v in desc.get("default_headers", {}).items():
            cmd_parts.append(f'-H "{k}: {v}"')

        # 端点特定请求头
        for k, v in ep.get("headers", {}).items():
            cmd_parts.append(f'-H "{k}: {v}"')

        # 请求体
        if ep.get("body") is not None:
            body_str = json.dumps(ep["body"], ensure_ascii=False)
            cmd_parts.append(f"-d '{body_str}'")

        # 期望状态码提示
        lines.append(f'echo "期望状态码: {ep.get("expect_status", 200)}"')
        lines.append(" ".join(cmd_parts) + " | python3 -m json.tool 2>/dev/null || " + " ".join(cmd_parts))
        lines.append("")
        lines.append('echo ""')
        lines.append("")

    content = "\n".join(lines) + "\n"
    filepath = os.path.join(output_dir, "api_calls.sh")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(filepath, 0o755)
    return filepath


# ============================================================
# Python unittest 生成
# ============================================================

def generate_python(desc, output_dir, timeout=10):
    """生成 Python unittest 测试脚本"""
    lines = []
    lines.append("#!/usr/bin/env python3")
    lines.append("# -*- coding: utf-8 -*-")
    lines.append('"""')
    lines.append("API 自动化测试脚本")
    lines.append(f"自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"基础 URL: {desc['base_url']}")
    lines.append('"""')
    lines.append("")
    lines.append("import unittest")
    lines.append("import json")
    lines.append("import time")
    lines.append("import urllib.request")
    lines.append("import urllib.error")
    lines.append("import urllib.parse")
    lines.append("import os")
    lines.append("")
    lines.append(f'BASE_URL = os.environ.get("API_BASE_URL", "{desc["base_url"]}")')
    lines.append(f"TIMEOUT = {timeout}")
    lines.append("")

    # 认证
    auth = desc.get("auth", {})
    if auth.get("type") == "bearer":
        token = auth.get("token", "")
        lines.append(f'TOKEN = os.environ.get("API_TOKEN", "{token}")')
        lines.append('AUTH_HEADER = {"Authorization": f"Bearer {TOKEN}"}')
    elif auth.get("type") == "apikey":
        key = auth.get("key", "")
        header_name = auth.get("header", "X-API-Key")
        lines.append(f'API_KEY = os.environ.get("API_KEY", "{key}")')
        lines.append(f'AUTH_HEADER = {{"{header_name}": API_KEY}}')
    else:
        lines.append("AUTH_HEADER = {}")

    lines.append("")

    # 默认请求头
    default_headers = desc.get("default_headers", {})
    lines.append(f"DEFAULT_HEADERS = {json.dumps(default_headers, ensure_ascii=False)}")
    lines.append("")

    # 测试类
    lines.append("")
    lines.append("def make_request(method, path, params=None, body=None, headers=None):")
    lines.append('    """发送 HTTP 请求并返回 (status_code, response_data, elapsed)"""'
)
    lines.append("    url = BASE_URL + path")
    lines.append("    if params:")
    lines.append("        url += '?' + urllib.parse.urlencode(params)")
    lines.append("")
    lines.append("    all_headers = {}")
    lines.append("    all_headers.update(DEFAULT_HEADERS)")
    lines.append("    all_headers.update(AUTH_HEADER)")
    lines.append("    if headers:")
    lines.append("        all_headers.update(headers)")
    lines.append("")
    lines.append("    data = None")
    lines.append("    if body is not None:")
    lines.append("        data = json.dumps(body, ensure_ascii=False).encode('utf-8')")
    lines.append("        all_headers.setdefault('Content-Type', 'application/json')")
    lines.append("")
    lines.append("    req = urllib.request.Request(url, data=data, headers=all_headers, method=method)")
    lines.append("    start = time.time()")
    lines.append("    try:")
    lines.append("        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:")
    lines.append("            status = resp.status")
    lines.append("            raw = resp.read().decode('utf-8')")
    lines.append("    except urllib.error.HTTPError as e:")
    lines.append("        status = e.code")
    lines.append("        raw = e.read().decode('utf-8', errors='replace')")
    lines.append("    elapsed = time.time() - start")
    lines.append("")
    lines.append("    try:")
    lines.append("        data = json.loads(raw) if raw else None")
    lines.append("    except (json.JSONDecodeError, ValueError):")
    lines.append("        data = raw")
    lines.append("")
    lines.append("    return status, data, elapsed")
    lines.append("")
    lines.append("")
    lines.append("class TestAPI(unittest.TestCase):")
    lines.append('    """API 自动化测试"""')
    lines.append("")

    # 生成每个端点的测试方法
    for i, ep in enumerate(desc["endpoints"], 1):
        method = ep["method"].upper()
        path = ep["path"]
        name = ep.get("name", f"{method} {path}")
        safe_name = f"test_{i:02d}_{method.lower()}_{path.strip('/').replace('/', '_').replace('-', '_').replace('{', '').replace('}', '')}"
        if not safe_name[5:].replace('_', '').isalnum():
            safe_name = f"test_{i:02d}_{method.lower()}"

        lines.append(f"    def {safe_name}(self):")
        lines.append(f'        """{name}"""')
        lines.append(f'        status, data, elapsed = make_request(')
        lines.append(f'            "{method}",')
        lines.append(f'            "{path}",')

        if ep.get("params"):
            lines.append(f'            params={json.dumps(ep["params"], ensure_ascii=False)},')
        else:
            lines.append(f'            params=None,')

        if ep.get("body") is not None:
            lines.append(f'            body={json.dumps(ep["body"], ensure_ascii=False)},')
        else:
            lines.append(f'            body=None,')

        if ep.get("headers"):
            lines.append(f'            headers={json.dumps(ep["headers"], ensure_ascii=False)},')
        else:
            lines.append(f'            headers=None,')

        lines.append(f'        )')
        lines.append("")

        # 状态码断言
        expect_status = ep.get("expect_status", 200)
        lines.append(f'        self.assertEqual(status, {expect_status},')
        lines.append(f'                         f"期望状态码 {expect_status}，实际 {{status}}，响应: {{data}}")')

        # JSON 字段断言
        expect_fields = ep.get("expect_fields", [])
        if expect_fields:
            lines.append('        self.assertIsInstance(data, dict, f"响应不是 JSON 对象: {data}")')
            for field in expect_fields:
                lines.append(f'        self.assertIn("{field}", data, f"响应缺少字段: {field}")')

        # 响应时间断言
        max_rt = ep.get("max_response_time")
        if max_rt:
            lines.append(f'        self.assertLess(elapsed, {max_rt},')
            lines.append(f'                         f"响应时间 {{elapsed:.3f}}s 超过上限 {max_rt}s")')

        lines.append("")

    # 报告生成（如果 --run --report）
    lines.append("")
    lines.append("def run_with_report():")
    lines.append('    """运行测试并生成报告"""')
    lines.append("    import io")
    lines.append("    from unittest import TextTestRunner, TestLoader")
    lines.append("    stream = io.StringIO()")
    lines.append("    runner = TextTestRunner(stream=stream, verbosity=2)")
    lines.append("    suite = TestLoader().loadTestsFromTestCase(TestAPI)")
    lines.append("    result = runner.run(suite)")
    lines.append("    output = stream.getvalue()")
    lines.append("    print(output)")
    lines.append("    return result, output")
    lines.append("")
    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append('    if "--report" in sys.argv:')
    lines.append("        run_with_report()")
    lines.append("    else:")
    lines.append("        unittest.main(verbosity=2)")

    content = "\n".join(lines) + "\n"
    filepath = os.path.join(output_dir, "test_api.py")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    os.chmod(filepath, 0o755)
    return filepath


# ============================================================
# Postman 集合生成
# ============================================================

def generate_postman(desc, output_dir):
    """生成 Postman Collection v2.1"""
    collection = {
        "info": {
            "name": desc.get("name", "API Test Suite"),
            "_postman_id": "auto-generated-" + str(int(time.time())),
            "description": f"自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [],
        "variable": [
            {"key": "base_url", "value": desc["base_url"]},
        ],
    }

    auth = desc.get("auth", {})
    if auth.get("type") == "bearer":
        collection["auth"] = {
            "type": "bearer",
            "bearer": [{"key": "token", "value": auth.get("token", ""), "type": "string"}],
        }
        collection["variable"].append({"key": "token", "value": auth.get("token", "")})

    for ep in desc["endpoints"]:
        method = ep["method"].upper()
        path = ep["path"]
        name = ep.get("name", f"{method} {path}")

        item = {
            "name": name,
            "request": {
                "method": method,
                "header": [],
                "url": {
                    "raw": "{{base_url}}" + path,
                    "host": ["{{base_url}}"],
                    "path": path.strip("/").split("/"),
                },
            },
        }

        # 请求头
        for k, v in desc.get("default_headers", {}).items():
            item["request"]["header"].append({"key": k, "value": v})
        for k, v in ep.get("headers", {}).items():
            item["request"]["header"].append({"key": k, "value": v})

        # 查询参数
        if ep.get("params"):
            item["request"]["url"]["query"] = [
                {"key": k, "value": str(v)} for k, v in ep["params"].items()
            ]

        # 请求体
        if ep.get("body") is not None:
            item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(ep["body"], ensure_ascii=False, indent=2),
                "options": {"raw": {"language": "json"}},
            }

        # 测试脚本（Postman 预请求脚本）
        expect_status = ep.get("expect_status", 200)
        expect_fields = ep.get("expect_fields", [])
        test_script = []
        test_script.append(f'pm.test("Status code is {expect_status}", function () {{')
        test_script.append(f'    pm.response.to.have.status({expect_status});')
        test_script.append('});')
        for field in expect_fields:
            test_script.append(f'pm.test("Response has field {field}", function () {{')
            test_script.append(f'    var json = pm.response.json();')
            test_script.append(f'    pm.expect(json).to.have.property("{field}");')
            test_script.append('});')

        item["event"] = [{
            "listen": "test",
            "script": {"type": "text/javascript", "exec": test_script},
        }]

        collection["item"].append(item)

    content = json.dumps(collection, ensure_ascii=False, indent=2)
    filepath = os.path.join(output_dir, "postman_collection.json")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


# ============================================================
# 测试执行与报告
# ============================================================

def run_tests(desc, timeout=10):
    """直接执行测试，返回结果列表"""
    results = []
    auth = desc.get("auth", {})

    base_headers = dict(desc.get("default_headers", {}))
    if auth.get("type") == "bearer":
        base_headers["Authorization"] = f"Bearer {auth.get('token', '')}"
    elif auth.get("type") == "apikey":
        header_name = auth.get("header", "X-API-Key")
        base_headers[header_name] = auth.get("key", "")

    for ep in desc["endpoints"]:
        method = ep["method"].upper()
        path = ep["path"]
        name = ep.get("name", f"{method} {path}")

        url = desc["base_url"] + path
        if ep.get("params"):
            url += "?" + urllib.parse.urlencode(ep["params"])

        headers = dict(base_headers)
        headers.update(ep.get("headers", {}))

        data = None
        if ep.get("body") is not None:
            data = json.dumps(ep["body"], ensure_ascii=False).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        start = time.time()
        status = None
        response_data = None
        error = None

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read().decode("utf-8", errors="replace")
        except Exception as e:
            error = str(e)
            raw = ""

        elapsed = time.time() - start

        try:
            response_data = json.loads(raw) if raw else None
        except (json.JSONDecodeError, ValueError):
            response_data = raw

        # 断言检查
        passed = True
        failures = []

        expect_status = ep.get("expect_status", 200)
        if status != expect_status:
            passed = False
            failures.append(f"状态码: 期望 {expect_status}，实际 {status}")

        expect_fields = ep.get("expect_fields", [])
        if expect_fields and isinstance(response_data, dict):
            for field in expect_fields:
                if field not in response_data:
                    passed = False
                    failures.append(f"缺少字段: {field}")

        max_rt = ep.get("max_response_time")
        if max_rt and elapsed > max_rt:
            passed = False
            failures.append(f"响应时间: {elapsed:.3f}s > {max_rt}s")

        if error:
            passed = False
            failures.append(f"请求异常: {error}")

        results.append({
            "name": name,
            "method": method,
            "path": path,
            "status": status,
            "elapsed": elapsed,
            "passed": passed,
            "failures": failures,
            "response": response_data if not passed else None,
        })

    return results


def generate_report(results, output_dir, desc):
    """生成 HTML 和 Markdown 测试报告"""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0

    # Markdown 报告
    md_lines = []
    md_lines.append("# API 测试报告")
    md_lines.append("")
    md_lines.append(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append(f"**基础 URL**: {desc['base_url']}")
    md_lines.append(f"**总用例数**: {total}")
    md_lines.append(f"**通过**: {passed}")
    md_lines.append(f"**失败**: {failed}")
    md_lines.append(f"**通过率**: {pass_rate:.1f}%")
    md_lines.append("")
    md_lines.append("## 详细结果")
    md_lines.append("")
    md_lines.append("| # | 用例 | 方法 | 路径 | 状态码 | 耗时 | 结果 |")
    md_lines.append("|---|---|---|---|---|---|---|")

    for i, r in enumerate(results, 1):
        status_icon = "✅" if r["passed"] else "❌"
        md_lines.append(
            f"| {i} | {r['name']} | {r['method']} | {r['path']} | "
            f"{r['status'] or 'N/A'} | {r['elapsed']:.3f}s | {status_icon} |"
        )

    if failed > 0:
        md_lines.append("")
        md_lines.append("## 失败详情")
        md_lines.append("")
        for r in results:
            if not r["passed"]:
                md_lines.append(f"### ❌ {r['name']}")
                for f in r["failures"]:
                    md_lines.append(f"- {f}")
                if r["response"]:
                    md_lines.append(f"- 响应: `{json.dumps(r['response'], ensure_ascii=False)[:200]}`")
                md_lines.append("")

    md_content = "\n".join(md_lines) + "\n"
    md_path = os.path.join(output_dir, "test_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # HTML 报告
    html_lines = []
    html_lines.append("<!DOCTYPE html>")
    html_lines.append('<html lang="zh-CN">')
    html_lines.append("<head>")
    html_lines.append('<meta charset="UTF-8">')
    html_lines.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html_lines.append("<title>API 测试报告</title>")
    html_lines.append("<style>")
    html_lines.append("body{font-family:-apple-system,sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#1a1a2e;color:#eee;}")
    html_lines.append("h1{color:#00d4ff;}")
    html_lines.append(".summary{display:flex;gap:20px;margin:20px 0;flex-wrap:wrap;}")
    html_lines.append(".card{background:#16213e;padding:15px 25px;border-radius:10px;flex:1;min-width:120px;}")
    html_lines.append(".card .num{font-size:2em;font-weight:bold;}")
    html_lines.append(".card .label{color:#aaa;font-size:0.9em;}")
    html_lines.append(".pass{color:#4ade80;} .fail{color:#f87171;}")
    html_lines.append("table{width:100%;border-collapse:collapse;margin-top:20px;}")
    html_lines.append("th,td{padding:10px;text-align:left;border-bottom:1px solid #333;}")
    html_lines.append("th{background:#0f3460;color:#00d4ff;}")
    html_lines.append("tr:hover{background:#16213e;}")
    html_lines.append(".fail-detail{background:#3d1a1a;padding:10px;border-radius:5px;margin:5px 0;}")
    html_lines.append("</style>")
    html_lines.append("</head>")
    html_lines.append("<body>")
    html_lines.append("<h1>API 测试报告</h1>")
    html_lines.append(f"<p>生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')} | 基础 URL: {html_mod.escape(desc['base_url'])}</p>")
    html_lines.append('<div class="summary">')
    html_lines.append(f'<div class="card"><div class="num">{total}</div><div class="label">总用例</div></div>')
    html_lines.append(f'<div class="card"><div class="num pass">{passed}</div><div class="label">通过</div></div>')
    html_lines.append(f'<div class="card"><div class="num fail">{failed}</div><div class="label">失败</div></div>')
    html_lines.append(f'<div class="card"><div class="num">{pass_rate:.1f}%</div><div class="label">通过率</div></div>')
    html_lines.append("</div>")
    html_lines.append("<h2>详细结果</h2>")
    html_lines.append("<table>")
    html_lines.append("<tr><th>#</th><th>用例</th><th>方法</th><th>路径</th><th>状态码</th><th>耗时</th><th>结果</th></tr>")

    for i, r in enumerate(results, 1):
        status_class = "pass" if r["passed"] else "fail"
        status_icon = "✅" if r["passed"] else "❌"
        html_lines.append(
            f"<tr><td>{i}</td><td>{html_mod.escape(r['name'])}</td>"
            f"<td>{r['method']}</td><td>{html_mod.escape(r['path'])}</td>"
            f"<td>{r['status'] or 'N/A'}</td><td>{r['elapsed']:.3f}s</td>"
            f"<td class='{status_class}'>{status_icon}</td></tr>"
        )
        if not r["passed"]:
            fail_text = "; ".join(r["failures"])
            html_lines.append(f"<tr><td colspan='7'><div class='fail-detail'>{html_mod.escape(fail_text)}</div></td></tr>")

    html_lines.append("</table>")
    html_lines.append("</body></html>")

    html_content = "\n".join(html_lines)
    html_path = os.path.join(output_dir, "test_report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return md_path, html_path, passed, failed, total, pass_rate


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="API 测试生成器（支持 curl/Python/Postman 三种格式）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s --input api.json --format python
  %(prog)s --input api.json --format all --output tests/
  %(prog)s --input api.json --format python --run --report
  %(prog)s --input api.json --format curl --token mytoken
        """,
    )

    parser.add_argument("--input", "-i", required=True, help="API 描述文件路径（JSON）")
    parser.add_argument("--format", "-f", default="python",
                        choices=["curl", "python", "postman", "all"],
                        help="输出格式（默认 python）")
    parser.add_argument("--output", "-o", default="./api_tests", help="输出目录")
    parser.add_argument("--base-url", help="覆盖基础 URL")
    parser.add_argument("--token", help="Bearer Token（覆盖描述文件中的值）")
    parser.add_argument("--run", action="store_true", help="生成后立即执行测试")
    parser.add_argument("--report", action="store_true", help="生成测试报告（需配合 --run）")
    parser.add_argument("--timeout", type=int, default=10, help="请求超时秒数（默认 10）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 加载描述
    desc = load_api_description(args.input)

    # 覆盖参数
    if args.base_url:
        desc["base_url"] = args.base_url
    if args.token:
        desc.setdefault("auth", {})["type"] = "bearer"
        desc["auth"]["token"] = args.token

    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)

    generated_files = []

    # 生成对应格式
    if args.format in ("curl", "all"):
        path = generate_curl(desc, args.output)
        generated_files.append(path)
        print(f"✅ curl 脚本: {path}")

    if args.format in ("python", "all"):
        path = generate_python(desc, args.output, args.timeout)
        generated_files.append(path)
        print(f"✅ Python 测试脚本: {path}")

    if args.format in ("postman", "all"):
        path = generate_postman(desc, args.output)
        generated_files.append(path)
        print(f"✅ Postman 集合: {path}")

    # 执行测试
    if args.run:
        print(f"\n🚀 开始执行 {len(desc['endpoints'])} 个测试用例...")
        print(f"   基础 URL: {desc['base_url']}")
        print("")

        results = run_tests(desc, args.timeout)

        for i, r in enumerate(results, 1):
            status_icon = "✅" if r["passed"] else "❌"
            print(f"  {status_icon} [{i}/{len(results)}] {r['name']}")
            print(f"     {r['method']} {r['path']} → 状态码 {r['status']}, 耗时 {r['elapsed']:.3f}s")
            if not r["passed"]:
                for f in r["failures"]:
                    print(f"     ❌ {f}")

        passed = sum(1 for r in results if r["passed"])
        total = len(results)
        print(f"\n📊 结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")

        # 生成报告
        if args.report:
            md_path, html_path, p, f, t, rate = generate_report(results, args.output, desc)
            print(f"\n📄 报告已生成:")
            print(f"   Markdown: {md_path}")
            print(f"   HTML:     {html_path}")

    print(f"\n📁 输出目录: {os.path.abspath(args.output)}")
    print(f"📦 生成文件: {len(generated_files)} 个")


if __name__ == "__main__":
    main()
