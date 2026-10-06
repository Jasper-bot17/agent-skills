#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git 提交信息生成助手 - Diff 分析脚本

解析 git diff 输出，提取变更统计、推断提交类型和影响范围、
提取关键变更点，为 AI 生成规范提交信息提供结构化输入。

用法：
    git diff --cached | python3 analyze_diff.py
    git diff HEAD~1 | python3 analyze_diff.py
    python3 analyze_diff.py --input changes.diff
    python3 analyze_diff.py --input changes.diff --format json
    python3 analyze_diff.py --input changes.diff --format text
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple


# ============================================================
# 数据结构
# ============================================================

@dataclass
class FileChange:
    """单个文件的变更信息"""
    path: str
    status: str  # added, modified, deleted, renamed
    additions: int = 0
    deletions: int = 0
    added_lines: List[str] = field(default_factory=list)
    deleted_lines: List[str] = field(default_factory=list)
    extension: str = ""

    @property
    def total_changes(self) -> int:
        return self.additions + self.deletions


@dataclass
class DiffAnalysis:
    """完整的 diff 分析结果"""
    files: List[FileChange] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    total_files: int = 0
    inferred_type: str = ""
    inferred_scope: str = ""
    type_confidence: str = ""  # high, medium, low
    key_changes: List[str] = field(default_factory=list)
    potential_breaking_changes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


# ============================================================
# 文件扩展名到语言/类型的映射
# ============================================================

EXTENSION_MAP = {
    # 源代码
    '.py': 'python', '.js': 'javascript', '.jsx': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript', '.java': 'java',
    '.go': 'go', '.rs': 'rust', '.c': 'c', '.cpp': 'cpp',
    '.cs': 'csharp', '.php': 'php', '.rb': 'ruby', '.swift': 'swift',
    '.kt': 'kotlin', '.scala': 'scala', '.r': 'r', '.m': 'objective-c',
    # 前端
    '.html': 'html', '.css': 'css', '.scss': 'css', '.sass': 'css',
    '.less': 'css', '.vue': 'vue', '.svelte': 'svelte',
    # 数据/配置
    '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.toml': 'toml',
    '.xml': 'xml', '.csv': 'csv', '.ini': 'ini', '.cfg': 'config',
    '.conf': 'config', '.env': 'config',
    # 文档
    '.md': 'markdown', '.rst': 'restructuredtext', '.txt': 'text',
    '.adoc': 'asciidoc',
    # 构建/CI
    'Dockerfile': 'docker', '.dockerfile': 'docker',
    'Makefile': 'makefile', 'CMakeLists.txt': 'cmake',
    # 测试
    '.test.js': 'test', '.test.ts': 'test', '.spec.js': 'test',
    '.spec.ts': 'test', '_test.go': 'test', '.test.py': 'test',
    '_test.py': 'test',
}

# 测试文件路径模式
TEST_PATH_PATTERNS = [
    r'/test[s]?/', r'/__tests__/', r'/spec[s]?/',
    r'\.test\.', r'\.spec\.', r'_test\.', r'test_',
]

# 文档文件路径模式
DOC_PATH_PATTERNS = [
    r'/doc[s]?/', r'/docs/', r'README', r'CHANGELOG',
    r'LICENSE', r'CONTRIBUTING', r'CODE_OF_CONDUCT',
]

# CI/CD 文件模式
CI_PATH_PATTERNS = [
    r'\.github/workflows/', r'\.gitlab-ci\.yml', r'Jenkinsfile',
    r'\.circleci/', r'\.travis\.yml', r'docker-compose',
    r'\.drone\.yml', r'azure-pipelines',
]

# 构建/依赖文件模式
BUILD_PATH_PATTERNS = [
    r'package\.json$', r'package-lock\.json$', r'yarn\.lock$',
    r'pnpm-lock\.yaml$', r'requirements\.txt$', r'Pipfile',
    r'pyproject\.toml$', r'setup\.py$', r'setup\.cfg$',
    r'Gemfile$', r'Cargo\.toml$', r'go\.mod$', r'go\.sum$',
    r'pom\.xml$', r'build\.gradle', r'build\.sbt$',
    r'webpack\.config', r'vite\.config', r'rollup\.config',
    r'tsconfig\.json$', r'jsconfig\.json$', r'\.babelrc',
    r'next\.config', r'nuxt\.config',
]

# 配置文件模式
CONFIG_PATH_PATTERNS = [
    r'\.gitignore$', r'\.eslintrc', r'\.prettierrc',
    r'\.editorconfig$', r'\.env', r'\.flake8',
    r'\.pylintrc', r'setup\.cfg$', r'\.mocharc',
    r'jest\.config', r'vitest\.config', r'cypress\.config',
    r'playwright\.config', r'postcss\.config', r'tailwind\.config',
]


# ============================================================
# Diff 解析器
# ============================================================

class DiffParser:
    """解析 unified diff 格式"""

    def __init__(self, diff_text: str):
        self.diff_text = diff_text
        self.files: List[FileChange] = []

    def parse(self) -> List[FileChange]:
        lines = self.diff_text.split('\n')
        i = 0
        current_file: Optional[FileChange] = None

        while i < len(lines):
            line = lines[i]

            # 新文件开始：diff --git a/path b/path
            if line.startswith('diff --git '):
                if current_file:
                    self.files.append(current_file)
                match = re.match(r'diff --git a/(.+?) b/(.+)', line)
                if match:
                    path = match.group(2)
                    current_file = FileChange(
                        path=path,
                        status='modified',
                        extension=self._get_extension(path),
                    )
                i += 1
                continue

            if current_file is None:
                i += 1
                continue

            # 文件状态检测
            if line.startswith('new file mode'):
                current_file.status = 'added'
            elif line.startswith('deleted file mode'):
                current_file.status = 'deleted'
            elif line.startswith('rename from'):
                current_file.status = 'renamed'
            elif line.startswith('Binary files'):
                current_file.status = 'binary'
                current_file.added_lines.append('[二进制文件变更]')

            # 变更行
            if line.startswith('+') and not line.startswith('+++'):
                current_file.additions += 1
                content = line[1:].strip()
                if content and len(content) < 200:
                    current_file.added_lines.append(content)
            elif line.startswith('-') and not line.startswith('---'):
                current_file.deletions += 1
                content = line[1:].strip()
                if content and len(content) < 200:
                    current_file.deleted_lines.append(content)

            i += 1

        if current_file:
            self.files.append(current_file)

        return self.files

    @staticmethod
    def _get_extension(path: str) -> str:
        """获取文件扩展名，处理特殊文件名"""
        basename = path.split('/')[-1]
        if basename in EXTENSION_MAP:
            return EXTENSION_MAP[basename]
        # 检查双扩展名如 .test.js
        for ext in ['.test.js', '.test.ts', '.spec.js', '.spec.ts',
                    '.test.py', '_test.go', '_test.py']:
            if basename.endswith(ext):
                return 'test'
        idx = basename.rfind('.')
        if idx > 0:
            return basename[idx:].lower()
        return ''


# ============================================================
# 提交类型推断
# ============================================================

class TypeInferrer:
    """根据变更文件和内容推断提交类型"""

    def __init__(self, files: List[FileChange]):
        self.files = files

    def infer(self) -> Tuple[str, str]:
        """返回 (type, confidence)"""
        scores: Dict[str, float] = defaultdict(float)

        for f in self.files:
            # 按路径模式判断
            if self._matches_any(f.path, TEST_PATH_PATTERNS) or f.extension == 'test':
                scores['test'] += 3
            if self._matches_any(f.path, DOC_PATH_PATTERNS) or f.extension in ('markdown', 'restructuredtext', 'asciidoc', 'text'):
                scores['docs'] += 3
            if self._matches_any(f.path, CI_PATH_PATTERNS):
                scores['ci'] += 4
            if self._matches_any(f.path, BUILD_PATH_PATTERNS):
                scores['build'] += 3
            if self._matches_any(f.path, CONFIG_PATH_PATTERNS):
                scores['chore'] += 2

            # 新增文件倾向 feat
            if f.status == 'added' and f.extension in ('py', 'js', 'ts', 'jsx', 'tsx', 'go', 'java', 'rs', 'vue'):
                scores['feat'] += 1.5

            # 删除文件倾向 refactor 或 chore
            if f.status == 'deleted':
                scores['refactor'] += 1
                scores['chore'] += 0.5

        # 内容层面判断
        all_added = '\n'.join(l for f in self.files for l in f.added_lines)
        all_deleted = '\n'.join(l for f in self.files for l in f.deleted_lines)

        # 检测 fix 关键词
        fix_keywords = [r'fix', r'bug', r'error', r'issue', r'修复', r'问题',
                         r'崩溃', r'异常', r'失败', r'crash', r'null', r'undefined',
                         r'边界', r'兼容', r'修复了', r'hotfix', r'patch']
        for kw in fix_keywords:
            if re.search(kw, all_added + all_deleted, re.IGNORECASE):
                scores['fix'] += 0.5
                break

        # 检测 perf 关键词
        perf_keywords = [r'perf', r'performance', r'优化', r'性能', r'缓存',
                          r'cache', r'索引', r'index', r'耗时', r'提速',
                          r'latency', r'throughput', r'qps']
        for kw in perf_keywords:
            if re.search(kw, all_added + all_deleted, re.IGNORECASE):
                scores['perf'] += 1
                break

        # 检测 refactor 关键词
        refactor_keywords = [r'refactor', r'rename', r'重构', r'提取', r'extract',
                              r'move', r'移动', r'拆分', r'split', r'合并', r'merge',
                              r'cleanup', r'清理', r'simplify', r'简化']
        for kw in refactor_keywords:
            if re.search(kw, all_added + all_deleted, re.IGNORECASE):
                scores['refactor'] += 1
                break

        # 纯格式变更检测（style）
        if self._is_style_only():
            scores['style'] += 5

        # 如果没有明显特征，根据变更量判断
        if not scores:
            total_added = sum(f.additions for f in self.files)
            total_deleted = sum(f.deletions for f in self.files)
            if total_added > total_deleted * 2 and total_added > 10:
                scores['feat'] = 1
            elif total_deleted > total_added * 2:
                scores['refactor'] = 1
            else:
                scores['fix'] = 0.5

        # 取最高分
        if scores:
            best_type = max(scores, key=scores.get)
            best_score = scores[best_type]
            second_score = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
            confidence = 'high' if best_score >= 3 and best_score > second_score * 1.5 else \
                         'medium' if best_score >= 2 else 'low'
            return best_type, confidence

        return 'chore', 'low'

    @staticmethod
    def _matches_any(path: str, patterns: List[str]) -> bool:
        return any(re.search(p, path, re.IGNORECASE) for p in patterns)

    def _is_style_only(self) -> bool:
        """判断是否为纯格式变更"""
        for f in self.files:
            if f.extension not in ('py', 'js', 'ts', 'jsx', 'tsx', 'css', 'scss', 'java', 'go'):
                return False
            # 检查变更行是否只包含空白/分号/import 排序变化
            for line in f.added_lines + f.deleted_lines:
                stripped = re.sub(r'[\s;,\(\)\{\}]', '', line)
                if stripped and not re.match(r'^(import|from|require|//|#|/\*|\*)', line):
                    # 有实际代码变更
                    if len(stripped) > 5:
                        return False
        # 所有文件都是小变更且主要是空白
        total = sum(f.total_changes for f in self.files)
        return total < 50


# ============================================================
# Scope 推断
# ============================================================

class ScopeInferrer:
    """从变更文件路径推断影响范围"""

    # 常见目录名到 scope 的映射
    SCOPE_MAP = {
        'auth': 'auth', 'authentication': 'auth', 'login': 'auth',
        'user': 'user', 'users': 'user', 'account': 'account',
        'order': 'order', 'orders': 'order', 'payment': 'payment',
        'pay': 'payment', 'product': 'product', 'products': 'product',
        'cart': 'cart', 'shopping': 'cart',
        'api': 'api', 'controller': 'api', 'controllers': 'api',
        'route': 'api', 'routes': 'api', 'endpoint': 'api',
        'service': 'service', 'services': 'service',
        'model': 'model', 'models': 'model', 'db': 'db',
        'database': 'db', 'migration': 'db', 'migrations': 'db',
        'config': 'config', 'configuration': 'config',
        'utils': 'utils', 'util': 'utils', 'helpers': 'utils',
        'helper': 'utils', 'common': 'common', 'shared': 'common',
        'components': 'ui', 'component': 'ui', 'ui': 'ui',
        'pages': 'ui', 'page': 'ui', 'views': 'ui', 'view': 'ui',
        'layouts': 'ui', 'layout': 'ui',
        'assets': 'assets', 'static': 'assets', 'public': 'assets',
        'styles': 'style', 'css': 'style', 'theme': 'style',
        'test': 'test', 'tests': 'test', 'spec': 'test',
        'docs': 'docs', 'doc': 'docs', 'documentation': 'docs',
        'scripts': 'scripts', 'script': 'scripts', 'tools': 'scripts',
        'ci': 'ci', 'deploy': 'ci', 'deployment': 'ci',
        'docker': 'ci', 'kubernetes': 'ci', 'k8s': 'ci',
        'notification': 'notification', 'notify': 'notification',
        'email': 'notification', 'sms': 'notification',
        'search': 'search', 'analytics': 'analytics',
        'report': 'report', 'reports': 'report',
        'export': 'export', 'import': 'import',
        'upload': 'upload', 'download': 'download',
        'file': 'file', 'files': 'file', 'storage': 'file',
        'cache': 'cache', 'queue': 'queue', 'job': 'queue',
        'worker': 'queue', 'task': 'queue',
        'log': 'log', 'logging': 'log', 'logger': 'log',
        'monitor': 'monitor', 'metrics': 'monitor',
        'alert': 'monitor', 'tracing': 'monitor',
        'i18n': 'i18n', 'locale': 'i18n', 'translation': 'i18n',
        'security': 'security', 'authz': 'security',
        'permission': 'security', 'role': 'security',
        'middleware': 'middleware', 'plugin': 'plugin',
        'extension': 'plugin', 'hook': 'plugin',
        'websocket': 'realtime', 'socket': 'realtime',
        'realtime': 'realtime', 'stream': 'realtime',
    }

    def infer(self, files: List[FileChange]) -> str:
        """推断最主要的 scope"""
        scope_counts: Dict[str, int] = defaultdict(int)

        for f in files:
            parts = f.path.lower().split('/')
            for part in parts:
                # 去掉扩展名
                part = re.sub(r'\.[^.]+$', '', part)
                if part in self.SCOPE_MAP:
                    scope_counts[self.SCOPE_MAP[part]] += f.total_changes

            # 检查文件名本身
            basename = parts[-1] if parts else ''
            basename_no_ext = re.sub(r'\.[^.]+$', '', basename)
            if basename_no_ext in self.SCOPE_MAP:
                scope_counts[self.SCOPE_MAP[basename_no_ext]] += f.total_changes

        if scope_counts:
            return max(scope_counts, key=scope_counts.get)

        # 如果没有匹配到已知 scope，取最顶层目录名
        top_dirs: Dict[str, int] = defaultdict(int)
        for f in files:
            parts = f.path.split('/')
            if len(parts) > 1:
                top_dirs[parts[0]] += f.total_changes

        if top_dirs:
            return max(top_dirs, key=top_dirs.get)

        return ''


# ============================================================
# 关键变更点提取
# ============================================================

class KeyChangeExtractor:
    """从新增/修改的代码行中提取关键变更点"""

    # 值得关注的代码模式
    INTERESTING_PATTERNS = [
        # 函数/方法定义
        (r'(?:def|function|func|fn|public|private|protected)\s+(\w+)\s*\(', '函数定义: {0}'),
        # 类定义
        (r'(?:class|interface|struct|enum)\s+(\w+)', '类型定义: {0}'),
        # 新增 API 路由
        (r'(?:app\.(?:get|post|put|delete|patch)|router\.(?:get|post|put|delete|patch)|@(?:Get|Post|Put|Delete|Patch)Mapping)\s*[\(]\s*["\']([^"\']+)', '新增接口: {0}'),
        # 常量/配置
        (r'(?:const|let|var)\s+(\w+)\s*=', '新增变量: {0}'),
        # 数据库表/字段
        (r'(?:CREATE TABLE|ALTER TABLE|ADD COLUMN)\s+(\w+)', '数据库变更: {0}'),
        # 导入新模块
        (r'(?:import|from)\s+(.+?)(?:\s+import|$)', '新增依赖: {0}'),
        # 错误处理
        (r'(?:try|catch|throw|raise|except)\b', '错误处理变更'),
        # 异步/并发
        (r'(?:async|await|Promise|goroutine|go\s+func)', '异步/并发变更'),
        # 正则
        (r'(?:new RegExp|re\.compile|Pattern\.compile)', '正则表达式变更'),
        # 加密/安全
        (r'(?:encrypt|decrypt|hash|salt|token|jwt|password|secret)', '安全相关变更'),
        # 日志
        (r'(?:console\.(?:log|error|warn)|logger\.(?:info|error|warn)|log\.Printf)', '日志变更'),
        # 注释中的 TODO/FIXME
        (r'(?:TODO|FIXME|HACK|XXX):?\s*(.+)', '待办: {0}'),
    ]

    def extract(self, files: List[FileChange], max_items: int = 15) -> List[str]:
        """提取关键变更点"""
        changes = []
        seen = set()

        for f in files:
            # 跳过测试和文档文件的详细分析
            if f.extension in ('markdown', 'test') or re.search(r'/test[s]?/', f.path):
                continue

            for line in f.added_lines:
                for pattern, template in self.INTERESTING_PATTERNS:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        try:
                            text = template.format(*match.groups()) if match.groups() else template
                        except (IndexError, KeyError):
                            text = template
                        if text not in seen and len(text) < 120:
                            seen.add(text)
                            changes.append(f"[{f.path}] {text}")
                        break

                if len(changes) >= max_items:
                    return changes

        return changes


# ============================================================
# 破坏性变更检测
# ============================================================

class BreakingChangeDetector:
    """检测潜在的破坏性变更"""

    BREAKING_PATTERNS = [
        # API 变更
        (r'(?:remove|delete|deprecate)\s+(?:api|endpoint|route|parameter|param|field)',
         '移除了 API/参数/字段，可能是破坏性变更'),
        (r'(?:改|变更).{0,10}(?:接口|API|返回|参数|字段)',
         '修改了接口/返回格式/参数，可能是破坏性变更'),
        # 数据库
        (r'(?:DROP|ALTER).{0,20}(?:TABLE|COLUMN|INDEX)',
         '数据库表/字段结构变更，可能是破坏性变更'),
        (r'(?:删除|移除).{0,10}(?:表|字段|列|索引)',
         '删除数据库表/字段，可能是破坏性变更'),
        # 配置
        (r'(?:remove|delete|rename).{0,20}(?:config|env|variable|option|setting)',
         '配置项变更/移除，可能是破坏性变更'),
        # 类型/接口
        (r'(?:interface|type|struct).{0,30}(?:remove|delete|change|rename)',
         '类型/接口定义变更，可能是破坏性变更'),
        # 版本
        (r'(?:v1|v2|version).{0,20}(?:upgrade|migrate|breaking)',
         '版本升级/迁移，可能是破坏性变更'),
        # 函数签名
        (r'(?:def|function|func).{0,50}\)\s*:',
         None),  # 函数签名变更需要对比，这里不直接判断
    ]

    def detect(self, files: List[FileChange]) -> List[str]:
        """检测潜在破坏性变更"""
        breaking = []
        seen = set()

        for f in files:
            all_lines = f.added_lines + f.deleted_lines
            for line in all_lines:
                for pattern, message in self.BREAKING_PATTERNS:
                    if message is None:
                        continue
                    if re.search(pattern, line, re.IGNORECASE):
                        if message not in seen:
                            seen.add(message)
                            breaking.append(f"[{f.path}] {message}")
                        break

            # 检测删除了导出的函数/类/接口
            for line in f.deleted_lines:
                if re.search(r'(?:export|public|def|function|class|interface)\s+\w+', line):
                    msg = f"[{f.path}] 删除了导出的符号，可能是破坏性变更"
                    if msg not in seen:
                        seen.add(msg)
                        breaking.append(msg)

        return breaking


# ============================================================
# 警告和建议
# ============================================================

class WarningDetector:
    """检测需要提醒用户的问题"""

    def detect(self, files: List[FileChange]) -> Tuple[List[str], List[str]]:
        """返回 (warnings, suggestions)"""
        warnings = []
        suggestions = []

        total_additions = sum(f.additions for f in files)
        total_deletions = sum(f.deletions for f in files)
        total_files = len(files)

        # 变更过大
        if total_additions + total_deletions > 500:
            warnings.append(f"本次变更较大（+{total_additions}/-{total_deletions}行，{total_files}个文件），建议拆分为多个提交")

        # 文件过多
        if total_files > 10:
            suggestions.append(f"涉及 {total_files} 个文件，确认是否需要拆分提交")

        # 敏感信息检测
        sensitive_patterns = [
            (r'(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']+["\']', '密码'),
            (r'(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*["\'][^"\']{8,}["\']', 'API Key/Token'),
            (r'(?:AKIA|AIza)[A-Za-z0-9]{16,}', 'AWS/Google 密钥'),
            (r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----', '私钥'),
            (r'(?:mongodb|mysql|postgres|redis)://[^:\s]+:[^@\s]+@', '数据库连接串（含密码）'),
        ]
        for f in files:
            for line in f.added_lines:
                for pattern, label in sensitive_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        warnings.append(f"[{f.path}] 检测到疑似{label}，请勿提交到版本控制！")
                        break

        # 大文件
        for f in files:
            if f.status == 'added' and f.total_changes > 200:
                suggestions.append(f"[{f.path}] 新增文件较大，确认是否应使用 Git LFS")

        # 缺少测试
        has_source = any(f.extension in ('py', 'js', 'ts', 'jsx', 'tsx', 'go', 'java')
                         and not re.search(r'/test[s]?/', f.path) for f in files)
        has_test = any(re.search(r'/test[s]?/|\.test\.|\.spec\.|_test\.', f.path) for f in files)
        if has_source and not has_test and total_additions > 30:
            suggestions.append("新增了源代码但未检测到测试文件，建议补充测试")

        # 仅修改注释但类型不是 docs
        all_code = '\n'.join(l for f in files for l in f.added_lines if f.extension in ('py', 'js', 'ts'))
        if all_code and all(re.match(r'^\s*(#|//|/\*|\*)', l) for l in all_code.split('\n') if l.strip()):
            suggestions.append("变更似乎仅涉及注释，建议使用 docs 类型")

        return warnings, suggestions


# ============================================================
# 主分析器
# ============================================================

class DiffAnalyzer:
    """整合所有分析模块"""

    def __init__(self, diff_text: str):
        self.diff_text = diff_text

    def analyze(self) -> DiffAnalysis:
        # 解析 diff
        parser = DiffParser(self.diff_text)
        files = parser.parse()

        if not files:
            return DiffAnalysis(warnings=["未检测到任何文件变更，请确认输入为有效的 git diff 格式"])

        # 统计
        total_additions = sum(f.additions for f in files)
        total_deletions = sum(f.deletions for f in files)

        # 推断类型
        type_inferrer = TypeInferrer(files)
        inferred_type, confidence = type_inferrer.infer()

        # 推断 scope
        scope_inferrer = ScopeInferrer()
        inferred_scope = scope_inferrer.infer(files)

        # 提取关键变更
        key_extractor = KeyChangeExtractor()
        key_changes = key_extractor.extract(files)

        # 检测破坏性变更
        breaking_detector = BreakingChangeDetector()
        breaking = breaking_detector.detect(files)

        # 警告和建议
        warning_detector = WarningDetector()
        warnings, suggestions = warning_detector.detect(files)

        return DiffAnalysis(
            files=files,
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_files=len(files),
            inferred_type=inferred_type,
            inferred_scope=inferred_scope,
            type_confidence=confidence,
            key_changes=key_changes,
            potential_breaking_changes=breaking,
            warnings=warnings,
            suggestions=suggestions,
        )


# ============================================================
# 输出格式化
# ============================================================

def format_text(analysis: DiffAnalysis) -> str:
    """格式化为人类可读的文本输出"""
    lines = []
    lines.append("=" * 60)
    lines.append("Git Diff 分析结果")
    lines.append("=" * 60)
    lines.append("")

    # 概览
    lines.append("【变更概览】")
    lines.append(f"  文件数: {analysis.total_files}")
    lines.append(f"  新增行: +{analysis.total_additions}")
    lines.append(f"  删除行: -{analysis.total_deletions}")
    lines.append("")

    # 文件列表
    lines.append("【变更文件】")
    status_icon = {'added': '+', 'modified': '~', 'deleted': '-', 'renamed': '→', 'binary': 'B'}
    for f in sorted(analysis.files, key=lambda x: x.total_changes, reverse=True):
        icon = status_icon.get(f.status, '?')
        lines.append(f"  {icon} {f.path}  (+{f.additions}/-{f.deletions})")
    lines.append("")

    # 推断结果
    lines.append("【推断提交类型】")
    scope_str = f"({analysis.inferred_scope})" if analysis.inferred_scope else ""
    lines.append(f"  建议类型: {analysis.inferred_type}{scope_str}")
    lines.append(f"  置信度: {analysis.type_confidence}")
    lines.append("")

    # 关键变更
    if analysis.key_changes:
        lines.append("【关键变更点】")
        for change in analysis.key_changes:
            lines.append(f"  - {change}")
        lines.append("")

    # 破坏性变更
    if analysis.potential_breaking_changes:
        lines.append("【⚠ 潜在破坏性变更】")
        for bc in analysis.potential_breaking_changes:
            lines.append(f"  ! {bc}")
        lines.append("")

    # 警告
    if analysis.warnings:
        lines.append("【警告】")
        for w in analysis.warnings:
            lines.append(f"  ⚠ {w}")
        lines.append("")

    # 建议
    if analysis.suggestions:
        lines.append("【建议】")
        for s in analysis.suggestions:
            lines.append(f"  💡 {s}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("注意：以上为自动分析结果，提交类型和内容需经人工确认。")
    lines.append("=" * 60)

    return "\n".join(lines)


def format_json(analysis: DiffAnalysis) -> str:
    """格式化为 JSON"""
    data = {
        "summary": {
            "total_files": analysis.total_files,
            "total_additions": analysis.total_additions,
            "total_deletions": analysis.total_deletions,
        },
        "inferred": {
            "type": analysis.inferred_type,
            "scope": analysis.inferred_scope,
            "confidence": analysis.type_confidence,
        },
        "files": [
            {
                "path": f.path,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions,
                "extension": f.extension,
            }
            for f in analysis.files
        ],
        "key_changes": analysis.key_changes,
        "potential_breaking_changes": analysis.potential_breaking_changes,
        "warnings": analysis.warnings,
        "suggestions": analysis.suggestions,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Git Diff 分析工具 - 为生成规范提交信息提供结构化输入"
    )
    parser.add_argument("--input", "-i", help="输入 diff 文件路径（默认从 stdin 读取）")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text",
                        help="输出格式（默认 text）")
    args = parser.parse_args()

    # 读取输入
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                diff_text = f.read()
        except FileNotFoundError:
            print(f"错误：文件 '{args.input}' 不存在", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"错误：读取文件失败 - {e}", file=sys.stderr)
            sys.exit(1)
    else:
        diff_text = sys.stdin.read()

    if not diff_text.strip():
        print("错误：输入为空，请提供 git diff 输出", file=sys.stderr)
        print("\n用法示例：", file=sys.stderr)
        print("  git diff --cached | python3 analyze_diff.py", file=sys.stderr)
        print("  git diff HEAD~1 | python3 analyze_diff.py", file=sys.stderr)
        print("  python3 analyze_diff.py --input changes.diff", file=sys.stderr)
        sys.exit(1)

    # 分析
    analyzer = DiffAnalyzer(diff_text)
    analysis = analyzer.analyze()

    # 输出
    if args.format == "json":
        print(format_json(analysis))
    else:
        print(format_text(analysis))


if __name__ == "__main__":
    main()
