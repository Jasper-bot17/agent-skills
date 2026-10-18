#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 自动化测试脚本
自动生成于 2026-10-18 20:36:26
基础 URL: https://api.example.com
"""

import unittest
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import os

BASE_URL = os.environ.get("API_BASE_URL", "https://api.example.com")
TIMEOUT = 10

TOKEN = os.environ.get("API_TOKEN", "test-token-123")
AUTH_HEADER = {"Authorization": f"Bearer {TOKEN}"}

DEFAULT_HEADERS = {"Content-Type": "application/json"}


def make_request(method, path, params=None, body=None, headers=None):
    """发送 HTTP 请求并返回 (status_code, response_data, elapsed)"""
    url = BASE_URL + path
    if params:
        url += '?' + urllib.parse.urlencode(params)

    all_headers = {}
    all_headers.update(DEFAULT_HEADERS)
    all_headers.update(AUTH_HEADER)
    if headers:
        all_headers.update(headers)

    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode('utf-8')
        all_headers.setdefault('Content-Type', 'application/json')

    req = urllib.request.Request(url, data=data, headers=all_headers, method=method)
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            raw = resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode('utf-8', errors='replace')
    elapsed = time.time() - start

    try:
        data = json.loads(raw) if raw else None
    except (json.JSONDecodeError, ValueError):
        data = raw

    return status, data, elapsed


class TestAPI(unittest.TestCase):
    """API 自动化测试"""

    def test_01_get_api_users(self):
        """获取用户列表"""
        status, data, elapsed = make_request(
            "GET",
            "/api/users",
            params={"page": 1, "limit": 10},
            body=None,
            headers=None,
        )

        self.assertEqual(status, 200,
                         f"期望状态码 200，实际 {status}，响应: {data}")
        self.assertIsInstance(data, dict, f"响应不是 JSON 对象: {data}")
        self.assertIn("data", data, f"响应缺少字段: data")
        self.assertIn("total", data, f"响应缺少字段: total")
        self.assertIn("page", data, f"响应缺少字段: page")

    def test_02_get_api_users_1(self):
        """获取用户详情"""
        status, data, elapsed = make_request(
            "GET",
            "/api/users/1",
            params=None,
            body=None,
            headers=None,
        )

        self.assertEqual(status, 200,
                         f"期望状态码 200，实际 {status}，响应: {data}")
        self.assertIsInstance(data, dict, f"响应不是 JSON 对象: {data}")
        self.assertIn("id", data, f"响应缺少字段: id")
        self.assertIn("name", data, f"响应缺少字段: name")
        self.assertIn("email", data, f"响应缺少字段: email")

    def test_03_post_api_users(self):
        """创建用户"""
        status, data, elapsed = make_request(
            "POST",
            "/api/users",
            params=None,
            body={"name": "测试用户", "email": "test@example.com", "age": 25},
            headers=None,
        )

        self.assertEqual(status, 201,
                         f"期望状态码 201，实际 {status}，响应: {data}")
        self.assertIsInstance(data, dict, f"响应不是 JSON 对象: {data}")
        self.assertIn("id", data, f"响应缺少字段: id")
        self.assertIn("name", data, f"响应缺少字段: name")
        self.assertIn("email", data, f"响应缺少字段: email")

    def test_04_put_api_users_1(self):
        """更新用户"""
        status, data, elapsed = make_request(
            "PUT",
            "/api/users/1",
            params=None,
            body={"name": "更新后的名字"},
            headers=None,
        )

        self.assertEqual(status, 200,
                         f"期望状态码 200，实际 {status}，响应: {data}")
        self.assertIsInstance(data, dict, f"响应不是 JSON 对象: {data}")
        self.assertIn("id", data, f"响应缺少字段: id")
        self.assertIn("name", data, f"响应缺少字段: name")

    def test_05_delete_api_users_1(self):
        """删除用户"""
        status, data, elapsed = make_request(
            "DELETE",
            "/api/users/1",
            params=None,
            body=None,
            headers=None,
        )

        self.assertEqual(status, 204,
                         f"期望状态码 204，实际 {status}，响应: {data}")


def run_with_report():
    """运行测试并生成报告"""
    import io
    from unittest import TextTestRunner, TestLoader
    stream = io.StringIO()
    runner = TextTestRunner(stream=stream, verbosity=2)
    suite = TestLoader().loadTestsFromTestCase(TestAPI)
    result = runner.run(suite)
    output = stream.getvalue()
    print(output)
    return result, output


if __name__ == "__main__":
    if "--report" in sys.argv:
        run_with_report()
    else:
        unittest.main(verbosity=2)
