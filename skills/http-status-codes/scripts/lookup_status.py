#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
HTTP 状态码速查助手

内置完整 HTTP 状态码数据库，支持按代码查询、分类浏览、关键词搜索、对比查询。
纯 Python 标准库实现，无外部依赖。

用法：
  python3 lookup_status.py 404
  python3 lookup_status.py --category 4xx
  python3 lookup_status.py --search "未授权"
  python3 lookup_status.py --compare 301 302
  python3 lookup_status.py --categories
  python3 lookup_status.py 500 --json
"""

import argparse
import json
import sys


# ============================================================
# HTTP 状态码数据库
# ============================================================

STATUS_CODES = {
    # ---- 1xx Informational ----
    100: {
        "name": "Continue",
        "zh_name": "继续",
        "category": "1xx Informational",
        "description": "请求者应继续发送请求体。服务器收到了请求头，等待请求体。",
        "causes": ["客户端使用 Expect: 100-continue 头，服务器确认可以继续"],
        "tips": ["确认请求体大小是否合理", "检查是否正确使用 Expect 头"],
        "example": "curl -H 'Expect: 100-continue' https://api.example.com/upload",
    },
    101: {
        "name": "Switching Protocols",
        "zh_name": "切换协议",
        "category": "1xx Informational",
        "description": "服务器同意切换协议（如从 HTTP/1.1 切换到 WebSocket）。",
        "causes": ["客户端请求升级协议（Upgrade 头）", "WebSocket 握手成功"],
        "tips": ["检查 Upgrade 和 Connection 头是否正确", "确认服务器支持目标协议"],
        "example": "curl -H 'Upgrade: websocket' -H 'Connection: Upgrade' https://api.example.com/ws",
    },
    102: {
        "name": "Processing",
        "zh_name": "处理中",
        "category": "1xx Informational",
        "description": "WebDAV 请求正在处理，暂未完成（RFC 2518）。",
        "causes": ["WebDAV 复杂请求耗时较长", "服务器正在执行多个操作"],
        "tips": ["等待服务器完成处理", "检查请求是否过于复杂"],
        "example": "WebDAV PROPFIND 请求可能返回此状态",
    },
    103: {
        "name": "Early Hints",
        "zh_name": "早期提示",
        "category": "1xx Informational",
        "description": "在最终响应前返回部分响应头（如 Link 头），用于预加载资源（RFC 8297）。",
        "causes": ["服务器在处理主请求时提前推送资源提示"],
        "tips": ["检查 Link 预加载头配置", "确认预加载资源是否正确"],
        "example": "HTTP/1.1 103 Early Hints\nLink: /style.css; rel=preload",
    },

    # ---- 2xx Success ----
    200: {
        "name": "OK",
        "zh_name": "成功",
        "category": "2xx Success",
        "description": "请求成功。返回的内容取决于请求方法（GET 返回资源，POST 返回操作结果）。",
        "causes": ["请求正常处理完成"],
        "tips": ["检查响应体是否符合预期格式", "确认 Content-Type 头"],
        "example": "curl https://api.example.com/users",
    },
    201: {
        "name": "Created",
        "zh_name": "已创建",
        "category": "2xx Success",
        "description": "请求成功并且服务器创建了新资源。通常在 POST 或 PUT 后返回。",
        "causes": ["POST 创建资源成功", "PUT 更新资源成功"],
        "tips": ["检查 Location 头获取新资源 URL", "确认创建的资源是否符合预期"],
        "example": "curl -X POST -d 'name=test' https://api.example.com/users",
    },
    202: {
        "name": "Accepted",
        "zh_name": "已接受",
        "category": "2xx Success",
        "description": "请求已接受处理，但尚未完成（异步任务）。",
        "causes": ["异步任务已接收，正在后台处理", "长时间运行的任务"],
        "tips": ["通过返回的任务 ID 查询处理进度", "确认任务状态查询接口"],
        "example": "curl -X POST https://api.example.com/jobs/process",
    },
    203: {
        "name": "Non-Authoritative Information",
        "zh_name": "非授权信息",
        "category": "2xx Success",
        "description": "返回的元信息来自缓存或第三方，不是原始服务器的标准响应。",
        "causes": ["代理或修改了响应内容", "缓存服务器返回的非权威信息"],
        "tips": ["检查是否经过代理服务器", "确认数据来源是否可信"],
        "example": "通过代理服务器获取资源时可能返回",
    },
    204: {
        "name": "No Content",
        "zh_name": "无内容",
        "category": "2xx Success",
        "description": "请求成功，但不返回任何响应体。常用于 DELETE 操作。",
        "causes": ["DELETE 成功", "PUT 更新成功且无需返回内容", "表单提交无返回"],
        "tips": ["确认前端正确处理空响应", "不要尝试解析响应体"],
        "example": "curl -X DELETE https://api.example.com/users/1",
    },
    205: {
        "name": "Reset Content",
        "zh_name": "重置内容",
        "category": "2xx Success",
        "description": "请求成功，要求请求者重置文档视图（如清空表单）。",
        "causes": ["表单提交成功，要求重置表单"],
        "tips": ["前端应清空表单输入", "不要保留之前的输入内容"],
        "example": "HTML 表单提交后返回，提示用户重新填写",
    },
    206: {
        "name": "Partial Content",
        "zh_name": "部分内容",
        "category": "2xx Success",
        "description": "服务器只返回了资源的部分内容（Range 请求）。",
        "causes": ["客户端使用 Range 头请求部分资源", "断点续传", "视频流播放"],
        "tips": ["检查 Content-Range 头", "确认返回的字节范围是否正确"],
        "example": "curl -H 'Range: bytes=0-1023' https://api.example.com/file",
    },
    207: {
        "name": "Multi-Status",
        "zh_name": "多状态",
        "category": "2xx Success",
        "description": "WebDAV：多个独立操作的状态码聚合在一个响应中（RFC 4918）。",
        "causes": ["WebDAV 批量操作", "多个资源同时操作"],
        "tips": ["解析 XML 响应中的各个状态", "检查每个子操作的状态码"],
        "example": "WebDAV PROPFIND 返回多个资源属性",
    },
    208: {
        "name": "Already Reported",
        "zh_name": "已报告",
        "category": "2xx Success",
        "description": "WebDAV：在 <dav:multistatus> 中已经枚举过，不再重复（RFC 5842）。",
        "causes": ["WebDAV 绑定循环检测", "避免重复枚举资源"],
        "tips": ["正常 WebDAV 行为，通常无需处理"],
        "example": "WebDAV BIND 请求返回",
    },
    226: {
        "name": "IM Used",
        "zh_name": "IM 已使用",
        "category": "2xx Success",
        "description": "服务器对资源执行了实例操作，返回了修改后的结果（RFC 3229）。",
        "causes": ["Delta 编码请求", "实例操作结果"],
        "tips": ["检查响应是否为计算后的结果"],
        "example": "GET with Instance-Manipulation header",
    },

    # ---- 3xx Redirection ----
    300: {
        "name": "Multiple Choices",
        "zh_name": "多种选择",
        "category": "3xx Redirection",
        "description": "请求的资源有多种可选表示形式。",
        "causes": ["资源有多种格式（如 JSON、XML）", "服务器提供多种版本"],
        "tips": ["检查响应中的可选列表", "通过 Accept 头指定偏好格式"],
        "example": "请求 /users 但服务器提供多种表示形式",
    },
    301: {
        "name": "Moved Permanently",
        "zh_name": "永久移动",
        "category": "3xx Redirection",
        "description": "请求的资源已永久移动到新 URL。以后应使用新 URL。",
        "causes": ["域名变更", "资源路径永久迁移", "HTTP 到 HTTPS 跳转"],
        "tips": ["更新书签和 API 端点", "SEO 权重转移到新 URL", "浏览器会缓存此跳转"],
        "example": "curl -L https://example.com/old-page",
    },
    302: {
        "name": "Found",
        "zh_name": "临时移动",
        "category": "3xx Redirection",
        "description": "请求的资源临时在另一个 URL。客户端应继续使用原 URL。",
        "causes": ["临时维护", "A/B 测试", "临时路由"],
        "tips": ["不要缓存此跳转", "POST 请求跳转后改为 GET"],
        "example": "curl -L https://example.com/temp-redirect",
    },
    303: {
        "name": "See Other",
        "zh_name": "参见其他",
        "category": "3xx Redirection",
        "description": "客户端应使用 GET 请求另一个 URL 来获取资源。",
        "causes": ["POST 后重定向到结果页面", "PRG 模式（Post/Redirect/Get）"],
        "tips": ["跳转后使用 GET 方法", "避免表单重复提交"],
        "example": "提交表单后跳转到成功页面",
    },
    304: {
        "name": "Not Modified",
        "zh_name": "未修改",
        "category": "3xx Redirection",
        "description": "资源未修改，客户端应使用缓存版本。",
        "causes": ["缓存验证（If-Modified-Since / If-None-Match）", "资源自上次请求后未变化"],
        "tips": ["使用本地缓存", "检查 ETag 和 Last-Modified 头"],
        "example": "curl -H 'If-None-Match: \"abc123\"' https://api.example.com/data",
    },
    305: {
        "name": "Use Proxy",
        "zh_name": "使用代理",
        "category": "3xx Redirection",
        "description": "请求的资源必须通过代理访问。已弃用。",
        "causes": ["服务器要求使用指定代理"],
        "tips": ["大多数客户端不再支持此状态码", "检查是否有代理配置问题"],
        "example": "已弃用状态码",
    },
    307: {
        "name": "Temporary Redirect",
        "zh_name": "临时重定向",
        "category": "3xx Redirection",
        "description": "与 302 类似，但保持原请求方法（POST 跳转后仍为 POST）。",
        "causes": ["临时维护", "负载均衡", "保持请求方法"],
        "tips": ["保持原始请求方法和请求体", "不要缓存"],
        "example": "curl -L -X POST https://example.com/temp-redirect",
    },
    308: {
        "name": "Permanent Redirect",
        "zh_name": "永久重定向",
        "category": "3xx Redirection",
        "description": "与 301 类似，但保持原请求方法（RFC 7538）。",
        "causes": ["永久迁移且保持请求方法", "API 版本升级"],
        "tips": ["更新 API 端点", "保持 POST 方法不变"],
        "example": "curl -L -X POST https://example.com/new-endpoint",
    },

    # ---- 4xx Client Error ----
    400: {
        "name": "Bad Request",
        "zh_name": "错误请求",
        "category": "4xx Client Error",
        "description": "请求有语法错误或参数错误，服务器无法处理。",
        "causes": ["JSON 格式错误", "缺少必需参数", "参数格式不正确", "请求头错误"],
        "tips": ["检查请求体 JSON 格式", "验证参数是否完整且类型正确", "查看服务器日志获取详细错误"],
        "example": "curl -X POST -d 'invalid json' https://api.example.com/users",
    },
    401: {
        "name": "Unauthorized",
        "zh_name": "未授权",
        "category": "4xx Client Error",
        "description": "请求要求用户身份验证。未登录或令牌无效。",
        "causes": ["未提供认证令牌", "令牌过期或无效", "登录已失效"],
        "tips": ["检查 Authorization 头", "确认令牌是否过期", "重新获取令牌"],
        "example": "curl -H 'Authorization: Bearer <token>' https://api.example.com/me",
    },
    402: {
        "name": "Payment Required",
        "zh_name": "需要付费",
        "category": "4xx Client Error",
        "description": "保留状态码，未来使用。目前部分 API 用于付费墙。",
        "causes": ["API 调用额度不足", "需要付费订阅"],
        "tips": ["检查账户余额和订阅状态", "查看 API 文档中的付费说明"],
        "example": "部分付费 API 返回",
    },
    403: {
        "name": "Forbidden",
        "zh_name": "禁止访问",
        "category": "4xx Client Error",
        "description": "服务器理解请求但拒绝执行。与 401 不同，认证无法解决。",
        "causes": ["权限不足", "IP 被封禁", "访问被策略禁止", "资源不允许访问"],
        "tips": ["检查账户权限", "确认 IP 是否被封禁", "查看服务器访问控制策略"],
        "example": "curl https://api.example.com/admin  # 普通用户访问管理接口",
    },
    404: {
        "name": "Not Found",
        "zh_name": "未找到",
        "category": "4xx Client Error",
        "description": "请求的资源不存在。",
        "causes": ["URL 路径错误", "资源已被删除", "ID 不存在", "域名/子路径错误"],
        "tips": ["检查 URL 拼写", "确认资源 ID 是否存在", "检查 API 基础路径"],
        "example": "curl https://api.example.com/users/999999",
    },
    405: {
        "name": "Method Not Allowed",
        "zh_name": "方法不允许",
        "category": "4xx Client Error",
        "description": "请求方法不被允许（如对只读资源发送 POST）。",
        "causes": ["使用了不支持的 HTTP 方法", "端点只支持 GET 但发送了 POST"],
        "tips": ["检查 Allow 头获取支持的方法列表", "确认 API 文档中的方法要求"],
        "example": "curl -X DELETE https://api.example.com/read-only",
    },
    406: {
        "name": "Not Acceptable",
        "zh_name": "不可接受",
        "category": "4xx Client Error",
        "description": "请求的 Accept 头指定的格式服务器无法返回。",
        "causes": ["Accept 头指定了不支持的格式", "内容协商失败"],
        "tips": ["检查 Accept 头", "尝试 Accept: application/json"],
        "example": "curl -H 'Accept: application/xml' https://api.example.com/data",
    },
    407: {
        "name": "Proxy Authentication Required",
        "zh_name": "需要代理认证",
        "category": "4xx Client Error",
        "description": "需要先通过代理服务器的认证。",
        "causes": ["代理服务器要求认证", "Nginx/Apache 代理配置"],
        "tips": ["配置 Proxy-Authorization 头", "检查代理认证设置"],
        "example": "通过需要认证的代理访问",
    },
    408: {
        "name": "Request Timeout",
        "zh_name": "请求超时",
        "category": "4xx Client Error",
        "description": "服务器等待请求超时。",
        "causes": ["客户端发送请求过慢", "网络延迟", "服务器超时设置过短"],
        "tips": ["检查网络连接", "增大客户端超时设置", "优化请求体大小"],
        "example": "上传大文件时连接中断",
    },
    409: {
        "name": "Conflict",
        "zh_name": "冲突",
        "category": "4xx Client Error",
        "description": "请求与资源当前状态冲突。",
        "causes": ["版本冲突（如乐观锁）", "重复创建", "并发修改", "数据约束冲突"],
        "tips": ["获取最新资源状态后重试", "检查并发修改问题", "查看冲突详情"],
        "example": "PUT /users/1 时 ETag 不匹配",
    },
    410: {
        "name": "Gone",
        "zh_name": "已删除",
        "category": "4xx Client Error",
        "description": "资源已永久删除，不再可用。与 404 不同，资源曾经存在过。",
        "causes": ["资源被永久删除", "域名迁移且旧内容不再保留"],
        "tips": ["从书签中删除", "不要再尝试访问", "SEO 中应移除链接"],
        "example": "curl https://example.com/deleted-page",
    },
    411: {
        "name": "Length Required",
        "zh_name": "需要内容长度",
        "category": "4xx Client Error",
        "description": "服务器要求 Content-Length 头。",
        "causes": ["POST/PUT 请求缺少 Content-Length", "服务器拒绝分块传输"],
        "tips": ["添加 Content-Length 头", "确认请求体大小"],
        "example": "curl -X POST -H 'Content-Length: 100' -d '...' https://api.example.com/upload",
    },
    412: {
        "name": "Precondition Failed",
        "zh_name": "前置条件失败",
        "category": "4xx Client Error",
        "description": "请求头中的条件评估为 false（If-Match、If-Unmodified-Since 等）。",
        "causes": ["条件请求失败", "ETag 不匹配", "资源已被修改"],
        "tips": ["获取最新 ETag 后重试", "检查条件头设置"],
        "example": "curl -H 'If-Match: \"old\"' -X PUT https://api.example.com/data",
    },
    413: {
        "name": "Payload Too Large",
        "zh_name": "载荷过大",
        "category": "4xx Client Error",
        "description": "请求体过大，服务器拒绝处理。",
        "causes": ["上传文件过大", "请求体超过服务器限制", "Nginx client_max_body_size 限制"],
        "tips": ["减小请求体大小", "分片上传", "调整服务器限制"],
        "example": "curl -X POST -F 'file=@large.iso' https://api.example.com/upload",
    },
    414: {
        "name": "URI Too Long",
        "zh_name": "URI 过长",
        "category": "4xx Client Error",
        "description": "请求的 URI 过长。",
        "causes": ["URL 参数过多", "GET 请求携带大量数据", "超长查询字符串"],
        "tips": ["改用 POST 方法", "缩短 URL 参数", "减小查询字符串"],
        "example": "curl 'https://api.example.com/search?q=' + 大量参数",
    },
    415: {
        "name": "Unsupported Media Type",
        "zh_name": "不支持的媒体类型",
        "category": "4xx Client Error",
        "description": "请求体格式不被服务器支持。",
        "causes": ["Content-Type 不支持", "发送了 XML 但 API 只接受 JSON"],
        "tips": ["检查 Content-Type 头", "使用 application/json", "查看 API 文档"],
        "example": "curl -H 'Content-Type: text/plain' -d 'data' https://api.example.com/users",
    },
    416: {
        "name": "Range Not Satisfiable",
        "zh_name": "范围不可满足",
        "category": "4xx Client Error",
        "description": "请求的 Range 范围无效。",
        "causes": ["Range 超出资源大小", "断点续传偏移量错误"],
        "tips": ["检查资源实际大小", "修正 Range 头"],
        "example": "curl -H 'Range: bytes=999999999' https://api.example.com/file",
    },
    417: {
        "name": "Expectation Failed",
        "zh_name": "预期失败",
        "category": "4xx Client Error",
        "description": "Expect 头指定的预期无法满足。",
        "causes": ["Expect: 100-continue 但服务器不支持", "请求体过大"],
        "tips": ["移除 Expect 头", "减小请求体"],
        "example": "curl -H 'Expect: 100-continue' https://api.example.com/large-upload",
    },
    418: {
        "name": "I'm a teapot",
        "zh_name": "我是茶壶",
        "category": "4xx Client Error",
        "description": "愚人节玩笑状态码（RFC 2324）。服务器拒绝煮咖啡。",
        "causes": ["彩蛋响应", "部分 API 用此表示拒绝"],
        "tips": ["通常无需处理", "了解即可"],
        "example": "curl https://tools.ietf.org/html/rfc2324",
    },
    421: {
        "name": "Misdirected Request",
        "zh_name": "错误定向请求",
        "category": "4xx Client Error",
        "description": "请求被发送到无法产生响应的服务器（RFC 7540, HTTP/2）。",
        "causes": ["HTTP/2 连接复用问题", "虚拟主机不匹配"],
        "tips": ["重新建立连接", "检查 SNI/Host 头"],
        "example": "HTTP/2 请求被路由到错误服务器",
    },
    422: {
        "name": "Unprocessable Entity",
        "zh_name": "无法处理的实体",
        "category": "4xx Client Error",
        "description": "请求格式正确但语义错误（WebDAV / JSON API）。",
        "causes": ["数据验证失败", "格式正确但业务逻辑错误", "字段值不合法"],
        "tips": ["检查业务规则", "查看响应中的验证错误详情", "修正字段值"],
        "example": "POST /users 但 email 格式不对",
    },
    423: {
        "name": "Locked",
        "zh_name": "已锁定",
        "category": "4xx Client Error",
        "description": "WebDAV：资源已被锁定（RFC 4918）。",
        "causes": ["WebDAV 资源被其他用户锁定"],
        "tips": ["等待锁释放", "解锁后重试"],
        "example": "WebDAV LOCK 后其他用户修改被拒",
    },
    424: {
        "name": "Failed Dependency",
        "zh_name": "依赖失败",
        "category": "4xx Client Error",
        "description": "WebDAV：由于前一个请求失败，当前请求无法执行。",
        "causes": ["批量操作中前序步骤失败"],
        "tips": ["检查前序操作结果", "修复依赖问题后重试"],
        "example": "WebDAV 批量操作中某个步骤失败",
    },
    425: {
        "name": "Too Early",
        "zh_name": "过早请求",
        "category": "4xx Client Error",
        "description": "服务器不愿意处理可能重放的请求（RFC 8470）。",
        "causes": ["重放攻击防护", "早期数据保护"],
        "tips": ["稍后重试", "检查 nonce 或时间戳"],
        "example": "HTTP/3 早期数据请求被拒",
    },
    426: {
        "name": "Upgrade Required",
        "zh_name": "需要升级",
        "category": "4xx Client Error",
        "description": "服务器要求客户端切换协议。",
        "causes": ["HTTP 到 HTTPS 强制升级", "协议版本不支持"],
        "tips": ["使用 HTTPS", "按 Upgrade 头要求切换协议"],
        "example": "curl https://api.example.com  # 被要求升级到 TLS",
    },
    428: {
        "name": "Precondition Required",
        "zh_name": "需要前置条件",
        "category": "4xx Client Error",
        "description": "服务器要求条件请求（RFC 6585）。",
        "causes": ["需要 ETag/If-Match 防止中间丢失更新"],
        "tips": ["添加 If-Match 头", "先获取资源的 ETag"],
        "example": "curl -H 'If-Match: \"etag\"' -X PUT https://api.example.com/data",
    },
    429: {
        "name": "Too Many Requests",
        "zh_name": "请求过多",
        "category": "4xx Client Error",
        "description": "请求频率超限。",
        "causes": ["触发 API 限流", "短时间请求过多", "QPS 超限"],
        "tips": ["查看 Retry-After 头", "降低请求频率", "实现指数退避重试", "检查配额"],
        "example": "curl -H 'Retry-After: 60' https://api.example.com/data",
    },
    431: {
        "name": "Request Header Fields Too Large",
        "zh_name": "请求头字段过大",
        "category": "4xx Client Error",
        "description": "请求头太大（RFC 6585）。",
        "causes": ["Cookie 过大", "请求头总长度超限", "URL 参数过长在头中"],
        "tips": ["减小 Cookie 大小", "精简请求头", "清理无用的请求头"],
        "example": "Cookie 超过 8KB",
    },
    451: {
        "name": "Unavailable For Legal Reasons",
        "zh_name": "因法律原因不可用",
        "category": "4xx Client Error",
        "description": "因法律要求（如政府审查）而不可用（RFC 7725）。",
        "causes": ["法律禁令", "版权要求下架", "地域限制"],
        "tips": ["查看响应中的法律原因", "确认是否有地域访问限制"],
        "example": "某地区访问受限内容",
    },

    # ---- 5xx Server Error ----
    500: {
        "name": "Internal Server Error",
        "zh_name": "服务器内部错误",
        "category": "5xx Server Error",
        "description": "服务器遇到意外情况，无法完成请求。",
        "causes": ["代码异常未捕获", "数据库连接失败", "第三方服务故障", "服务器配置错误"],
        "tips": ["查看服务器错误日志", "检查后端服务状态", "确认数据库连接", "检查依赖服务健康"],
        "example": "curl https://api.example.com/endpoint  # 后端抛出未捕获异常",
    },
    501: {
        "name": "Not Implemented",
        "zh_name": "未实现",
        "category": "5xx Server Error",
        "description": "服务器不支持请求的功能。",
        "causes": ["请求方法未实现", "功能尚未开发", "协议版本不支持"],
        "tips": ["检查 API 文档", "确认功能是否已上线", "使用支持的方法"],
        "example": "发送 PATCH 请求但服务器未实现",
    },
    502: {
        "name": "Bad Gateway",
        "zh_name": "错误网关",
        "category": "5xx Server Error",
        "description": "网关/代理从上游服务器收到无效响应。",
        "causes": ["后端服务崩溃", "Nginx 无法连接到后端", "上游服务返回了无效响应"],
        "tips": ["检查后端应用是否运行", "检查 Nginx/代理配置", "查看上游服务日志"],
        "example": "Nginx 反向代理到 5000 端口但后端未启动",
    },
    503: {
        "name": "Service Unavailable",
        "zh_name": "服务不可用",
        "category": "5xx Server Error",
        "description": "服务器暂时不可用（维护或过载）。",
        "causes": ["服务器维护中", "过载保护", "数据库连接池耗尽", "定时任务占用资源"],
        "tips": ["查看 Retry-After 头", "稍后重试", "检查服务健康状态", "检查负载"],
        "example": "curl https://api.example.com/health  # 维护页面",
    },
    504: {
        "name": "Gateway Timeout",
        "zh_name": "网关超时",
        "category": "5xx Server Error",
        "description": "网关/代理等待上游服务器响应超时。",
        "causes": ["后端处理过慢", "数据库查询超时", "第三方服务响应慢", "网络问题"],
        "tips": ["检查后端处理时间", "优化慢查询", "增大代理超时设置", "检查网络连接"],
        "example": "Nginx 等待 FastCGI 超时",
    },
    505: {
        "name": "HTTP Version Not Supported",
        "zh_name": "HTTP 版本不支持",
        "category": "5xx Server Error",
        "description": "服务器不支持请求的 HTTP 协议版本。",
        "causes": ["使用了过高的 HTTP 版本", "服务器只支持 HTTP/1.1 但发送了 HTTP/2"],
        "tips": ["降级 HTTP 版本", "检查服务器支持的版本"],
        "example": "HTTP/0.9 请求被现代服务器拒绝",
    },
    506: {
        "name": "Variant Also Negotiates",
        "zh_name": "变体协商",
        "category": "5xx Server Error",
        "description": "WebDAV：内容协商配置循环（RFC 2295）。",
        "causes": ["服务器内容协商配置错误"],
        "tips": ["检查服务器配置", "修正变体设置"],
        "example": "透明内容协商导致循环",
    },
    507: {
        "name": "Insufficient Storage",
        "zh_name": "存储空间不足",
        "category": "5xx Server Error",
        "description": "WebDAV：服务器存储空间不足无法完成请求（RFC 4918）。",
        "causes": ["磁盘满了", "存储配额超限", "上传文件过大"],
        "tips": ["检查磁盘空间", "清理旧文件", "调整存储配额"],
        "example": "WebDAV 上传文件时磁盘不足",
    },
    508: {
        "name": "Loop Detected",
        "zh_name": "检测到循环",
        "category": "5xx Server Error",
        "description": "WebDAV：检测到无限循环（RFC 5842）。",
        "causes": ["WebDAV 绑定循环", "重定向循环"],
        "tips": ["检查链接配置", "打破循环引用"],
        "example": "目录互相绑定导致循环",
    },
    510: {
        "name": "Not Extended",
        "zh_name": "未扩展",
        "category": "5xx Server Error",
        "description": "服务器需要扩展请求才能完成（RFC 2774）。",
        "causes": ["请求策略不满足", "需要额外扩展"],
        "tips": ["查看服务器要求的扩展", "补充所需扩展头"],
        "example": "服务器要求策略描述文件",
    },
    511: {
        "name": "Network Authentication Required",
        "zh_name": "需要网络认证",
        "category": "5xx Server Error",
        "description": "客户端需要进行网络认证才能访问（RFC 6585）。",
        "causes": [" captive portal（公共 WiFi 登录页）", "网络准入控制"],
        "tips": ["在浏览器中打开任意页面完成认证", "检查网络登录页面"],
        "example": "连接酒店 WiFi 后被重定向到登录页",
    },
}


# ============================================================
# 查询函数
# ============================================================

def lookup_code(code):
    """查询单个状态码"""
    code = int(code)
    if code in STATUS_CODES:
        return STATUS_CODES[code]
    return None


def list_by_category(category):
    """按分类列出状态码"""
    cat = category.lower().strip()
    # 支持 "2xx", "2", "2xx success" 等格式
    prefix = cat[:1] if cat[0].isdigit() else ""
    results = {}
    for code, info in sorted(STATUS_CODES.items()):
        if prefix and str(code).startswith(prefix):
            results[code] = info
    return results


def search_by_keyword(keyword):
    """按关键词搜索状态码"""
    kw = keyword.lower()
    results = {}
    for code, info in sorted(STATUS_CODES.items()):
        searchable = " ".join([
            info["name"], info["zh_name"], info["description"],
            info["category"], " ".join(info.get("causes", [])),
            " ".join(info.get("tips", [])),
        ]).lower()
        if kw in searchable:
            results[code] = info
    return results


def compare_codes(code1, code2):
    """对比两个状态码"""
    c1 = lookup_code(code1)
    c2 = lookup_code(code2)
    return c1, c2


# ============================================================
# 输出格式化
# ============================================================

def print_code(code, info, as_json=False):
    """打印单个状态码详情"""
    if as_json:
        output = {"code": code, **info}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"{'='*60}")
    print(f"  {code} {info['name']} ({info['zh_name']})")
    print(f"  分类: {info['category']}")
    print(f"{'='*60}")
    print(f"\n📖 描述: {info['description']}")
    print(f"\n🔍 常见原因:")
    for cause in info.get("causes", []):
        print(f"   • {cause}")
    print(f"\n💡 排查建议:")
    for tip in info.get("tips", []):
        print(f"   • {tip}")
    print(f"\n📝 示例: {info.get('example', 'N/A')}")
    print()


def print_category(cat_codes):
    """打印分类列表"""
    if not cat_codes:
        print("未找到该分类的状态码")
        return
    print(f"{'代码':<8} {'名称':<30} {'中文名称'}")
    print("-" * 60)
    for code, info in cat_codes.items():
        print(f"{code:<8} {info['name']:<30} {info['zh_name']}")
    print()


def print_search_results(results, keyword):
    """打印搜索结果"""
    if not results:
        print(f"未找到包含 '{keyword}' 的状态码")
        return
    print(f"🔍 搜索 '{keyword}' 找到 {len(results)} 个状态码:\n")
    for code, info in results.items():
        print(f"  {code} {info['name']} ({info['zh_name']})")
        print(f"     {info['description'][:60]}...")
    print()


def print_compare(c1, c2, code1, code2):
    """打印对比结果"""
    print(f"{'='*60}")
    print(f"  对比: {code1} {c1['name']}  vs  {code2} {c2['name']}")
    print(f"{'='*60}")
    print(f"\n  {code1} {c1['name']} ({c1['zh_name']}):")
    print(f"     {c1['description']}")
    print(f"\n  {code2} {c2['name']} ({c2['zh_name']}):")
    print(f"     {c2['description']}")
    print(f"\n  核心区别:")
    # 自动生成区别
    if c1["category"][0] != c2["category"][0]:
        print(f"     • 分类不同: {c1['category']} vs {c2['category']}")
    print(f"     • {c1['zh_name']}: {c1['causes'][0] if c1['causes'] else 'N/A'}")
    print(f"     • {c2['zh_name']}: {c2['causes'][0] if c2['causes'] else 'N/A'}")
    print()


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="HTTP 状态码速查助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s 404
  %(prog)s 200 404 500
  %(prog)s --category 4xx
  %(prog)s --search "未授权"
  %(prog)s --compare 301 302
  %(prog)s --categories
  %(prog)s 500 --json
        """,
    )

    parser.add_argument("codes", nargs="*", help="状态码（可多个）")
    parser.add_argument("--category", "-c", help="按分类列出（如 2xx, 4xx, 5xx）")
    parser.add_argument("--search", "-s", help="按关键词搜索")
    parser.add_argument("--compare", nargs=2, metavar=("CODE1", "CODE2"),
                        help="对比两个状态码")
    parser.add_argument("--categories", action="store_true", help="列出所有分类概要")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    # 列出所有分类
    if args.categories:
        print("HTTP 状态码分类概览\n")
        for cat in ["1", "2", "3", "4", "5"]:
            cat_codes = list_by_category(cat + "xx")
            cat_names = {
                "1": "1xx Informational（信息）",
                "2": "2xx Success（成功）",
                "3": "3xx Redirection（重定向）",
                "4": "4xx Client Error（客户端错误）",
                "5": "5xx Server Error（服务端错误）",
            }
            print(f"  {cat_names[cat]}: {len(cat_codes)} 个状态码")
            for code, info in list(cat_codes.items())[:3]:
                print(f"    - {code} {info['name']} ({info['zh_name']})")
            if len(cat_codes) > 3:
                print(f"    ... 等 {len(cat_codes)} 个")
            print()
        print(f"  共 {len(STATUS_CODES)} 个状态码\n")
        return

    # 按分类列出
    if args.category:
        cat_codes = list_by_category(args.category)
        print_category(cat_codes)
        return

    # 关键词搜索
    if args.search:
        results = search_by_keyword(args.search)
        print_search_results(results, args.search)
        return

    # 对比
    if args.compare:
        c1, c2 = compare_codes(args.compare[0], args.compare[1])
        if c1 is None or c2 is None:
            print("❌ 未找到指定的状态码")
            return
        print_compare(c1, c2, int(args.compare[0]), int(args.compare[1]))
        return

    # 查询状态码
    if args.codes:
        for code_str in args.codes:
            try:
                code = int(code_str)
            except ValueError:
                print(f"❌ 无效的状态码: {code_str}")
                continue
            info = lookup_code(code)
            if info is None:
                print(f"❌ 未找到状态码 {code}\n")
                continue
            print_code(code, info, as_json=args.json)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
