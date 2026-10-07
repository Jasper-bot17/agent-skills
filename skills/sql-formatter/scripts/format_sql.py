#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SQL 格式化与分析脚本

功能：
- SQL 格式化（关键字大写、缩进对齐、换行规范）
- 语法校验（括号匹配、关键字检查、常见错误检测）
- 表和列提取
- 查询结构解释
- 压缩输出
- 多种 SQL 方言支持（MySQL/PostgreSQL/SQLite/Oracle/SQL Server）

用法：
  python3 format_sql.py --file query.sql
  python3 format_sql.py --sql "select * from users where id=1"
  python3 format_sql.py --file query.sql --dialect mysql
  python3 format_sql.py --file query.sql --check
  python3 format_sql.py --file query.sql --extract
  python3 format_sql.py --file query.sql --explain
  python3 format_sql.py --file query.sql --minify
  python3 format_sql.py --file query.sql --output formatted.sql
  python3 format_sql.py --file query.sql --all
"""

import argparse
import re
import sys
from typing import Dict, List, Optional, Set, Tuple


# ============================================================
# SQL 关键字定义
# ============================================================

# 需要大写的关键字
SQL_KEYWORDS = {
    # 查询
    "SELECT", "FROM", "WHERE", "GROUP", "BY", "HAVING", "ORDER",
    "LIMIT", "OFFSET", "DISTINCT", "UNION", "INTERSECT", "EXCEPT",
    "ALL", "AS", "INTO",
    # 连接
    "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "CROSS", "ON", "USING",
    "NATURAL",
    # 条件
    "AND", "OR", "NOT", "IN", "EXISTS", "BETWEEN", "LIKE", "IS",
    "NULL", "TRUE", "FALSE", "UNKNOWN",
    # 聚合
    "COUNT", "SUM", "AVG", "MIN", "MAX",
    # 函数
    "COALESCE", "NULLIF", "CAST", "CONVERT", "CASE", "WHEN", "THEN",
    "ELSE", "END", "DECODE", "NVL", "IFNULL",
    # 数据操作
    "INSERT", "UPDATE", "DELETE", "MERGE", "VALUES", "SET",
    # 数据定义
    "CREATE", "ALTER", "DROP", "TABLE", "INDEX", "VIEW", "DATABASE",
    "SCHEMA", "SEQUENCE", "TRIGGER", "PROCEDURE", "FUNCTION",
    "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "UNIQUE", "CHECK",
    "DEFAULT", "CONSTRAINT", "AUTO_INCREMENT", "SERIAL",
    # 事务
    "BEGIN", "COMMIT", "ROLLBACK", "TRANSACTION", "SAVEPOINT",
    # 排序
    "ASC", "DESC",
    # 其他
    "WITH", "RECURSIVE", "ANY", "SOME", "OVER", "PARTITION", "WINDOW",
    "ROW", "ROWS", "RANGE", "PRECEDING", "FOLLOWING", "UNBOUNDED",
    "CURRENT", "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD",
    "FIRST_VALUE", "LAST_VALUE", "NTILE", "CUME_DIST", "PERCENT_RANK",
    "RETURNING", "CONFLICT", "DO", "NOTHING", "REPLACE",
}

# 顶层子句（触发换行和缩进减少）
TOP_LEVEL_CLAUSES = {
    "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING",
    "LIMIT", "OFFSET", "UNION", "UNION ALL", "INTERSECT", "EXCEPT",
    "INSERT INTO", "UPDATE", "DELETE FROM", "VALUES", "SET",
    "WITH", "RETURNING",
}

# JOIN 子句
JOIN_CLAUSES = {
    "JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN",
    "CROSS JOIN", "NATURAL JOIN", "LEFT OUTER JOIN", "RIGHT OUTER JOIN",
    "FULL OUTER JOIN",
}

# 支持的方言
DIALECTS = {"generic", "mysql", "postgresql", "sqlite", "oracle", "sqlserver"}


# ============================================================
# SQL 分词器
# ============================================================

class SQLToken:
    """SQL 词法单元"""
    def __init__(self, token_type: str, value: str, position: int):
        self.type = token_type  # keyword, identifier, string, number, operator, punctuation, whitespace, comment
        self.value = value
        self.position = position

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


def tokenize_sql(sql: str) -> List[SQLToken]:
    """将 SQL 文本分词"""
    tokens = []
    pos = 0
    n = len(sql)

    while pos < n:
        ch = sql[pos]

        # 空白
        if ch in " \t\n\r":
            start = pos
            while pos < n and sql[pos] in " \t\n\r":
                pos += 1
            tokens.append(SQLToken("whitespace", sql[start:pos], start))
            continue

        # 单行注释 --
        if ch == "-" and pos + 1 < n and sql[pos + 1] == "-":
            start = pos
            while pos < n and sql[pos] != "\n":
                pos += 1
            tokens.append(SQLToken("comment", sql[start:pos], start))
            continue

        # 多行注释 /* */
        if ch == "/" and pos + 1 < n and sql[pos + 1] == "*":
            start = pos
            pos += 2
            while pos < n - 1 and not (sql[pos] == "*" and sql[pos + 1] == "/"):
                pos += 1
            pos = min(pos + 2, n)
            tokens.append(SQLToken("comment", sql[start:pos], start))
            continue

        # 字符串 '...'
        if ch == "'":
            start = pos
            pos += 1
            while pos < n:
                if sql[pos] == "'":
                    if pos + 1 < n and sql[pos + 1] == "'":
                        pos += 2  # 转义的单引号
                        continue
                    pos += 1
                    break
                pos += 1
            tokens.append(SQLToken("string", sql[start:pos], start))
            continue

        # 双引号标识符 "..."
        if ch == '"':
            start = pos
            pos += 1
            while pos < n and sql[pos] != '"':
                pos += 1
            pos = min(pos + 1, n)
            tokens.append(SQLToken("identifier", sql[start:pos], start))
            continue

        # 反引号标识符 `...` (MySQL)
        if ch == "`":
            start = pos
            pos += 1
            while pos < n and sql[pos] != "`":
                pos += 1
            pos = min(pos + 1, n)
            tokens.append(SQLToken("identifier", sql[start:pos], start))
            continue

        # 数字
        if ch.isdigit() or (ch == "." and pos + 1 < n and sql[pos + 1].isdigit()):
            start = pos
            while pos < n and (sql[pos].isdigit() or sql[pos] in ".eE+-"):
                # 避免 + - 被误吞
                if sql[pos] in "+-" and pos > start and sql[pos - 1] not in "eE":
                    break
                pos += 1
            tokens.append(SQLToken("number", sql[start:pos], start))
            continue

        # 标识符/关键字
        if ch.isalpha() or ch == "_":
            start = pos
            while pos < n and (sql[pos].isalnum() or sql[pos] == "_"):
                pos += 1
            word = sql[start:pos]
            token_type = "keyword" if word.upper() in SQL_KEYWORDS else "identifier"
            tokens.append(SQLToken(token_type, word, start))
            continue

        # 操作符
        if ch in "=<>!+-*/%&|^~":
            start = pos
            # 多字符操作符
            if pos + 1 < n and sql[pos:pos + 2] in ("<=", ">=", "!=", "<>", "||", "::"):
                pos += 2
            else:
                pos += 1
            tokens.append(SQLToken("operator", sql[start:pos], start))
            continue

        # 标点
        if ch in "(),;.":
            tokens.append(SQLToken("punctuation", ch, pos))
            pos += 1
            continue

        # 其他字符（保留原样）
        tokens.append(SQLToken("other", ch, pos))
        pos += 1

    return tokens


# ============================================================
# SQL 格式化
# ============================================================

def format_sql(sql: str, indent: int = 4, dialect: str = "generic") -> str:
    """格式化 SQL"""
    tokens = tokenize_sql(sql)
    lines = []
    current_line = []
    indent_level = 0
    list_indent = 0  # 列列表缩进（SELECT/GROUP BY/ORDER BY 后的列）
    func_paren_depth = 0  # 函数调用括号深度
    i = 0

    def flush_line():
        nonlocal current_line
        if current_line:
            # 去除行尾空白
            line = "".join(current_line).rstrip()
            if line:
                total_indent = (indent_level + list_indent) * indent
                lines.append(" " * total_indent + line)
            current_line = []

    # 函数名集合（用于判断括号是否为函数调用）
    FUNCTION_NAMES = {"COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "NULLIF",
                      "CAST", "CONVERT", "CASE", "DECODE", "NVL", "IFNULL",
                      "GROUP_CONCAT", "CONCAT", "SUBSTRING", "TRIM", "UPPER",
                      "LOWER", "LENGTH", "ROUND", "FLOOR", "CEIL", "ABS",
                      "NOW", "CURDATE", "CURTIME", "DATE", "YEAR", "MONTH",
                      "DAY", "HOUR", "MINUTE", "SECOND", "EXTRACT", "DATE_FORMAT",
                      "IF", "IFNULL", "NULLIF", "GREATEST", "LEAST", "ROW_NUMBER",
                      "RANK", "DENSE_RANK", "LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE",
                      "NTILE", "CUME_DIST", "PERCENT_RANK", "OVER"}

    def is_function_call(idx: int) -> bool:
        """检查 idx 位置的 '(' 是否为函数调用"""
        j = idx - 1
        while j >= 0 and tokens[j].type == "whitespace":
            j -= 1
        if j >= 0:
            prev = tokens[j]
            if prev.type == "identifier":
                return True
            if prev.type == "keyword" and prev.value.upper() in FUNCTION_NAMES:
                return True
        return False

    while i < len(tokens):
        token = tokens[i]

        # 跳过多余空白
        if token.type == "whitespace":
            if current_line and not current_line[-1].endswith(" "):
                current_line.append(" ")
            i += 1
            continue

        # 注释单独成行
        if token.type == "comment":
            flush_line()
            lines.append(" " * (indent_level * indent) + token.value.strip())
            i += 1
            continue

        # 分号：结束语句
        if token.type == "punctuation" and token.value == ";":
            current_line.append(";")
            flush_line()
            lines.append("")  # 空行分隔语句
            indent_level = 0
            list_indent = 0
            i += 1
            continue

        # 左括号
        if token.type == "punctuation" and token.value == "(":
            if is_function_call(i):
                # 函数调用：不换行，保持在同一行
                current_line.append("(")
                func_paren_depth += 1
                i += 1
                continue
            else:
                # 子查询或表达式分组：换行并增加缩进
                current_line.append("(")
                flush_line()
                indent_level += 1
                i += 1
                continue

        # 右括号
        if token.type == "punctuation" and token.value == ")":
            if func_paren_depth > 0:
                # 函数调用的右括号：跟在当前行后面
                current_line.append(")")
                func_paren_depth -= 1
            else:
                flush_line()
                indent_level = max(0, indent_level - 1)
                current_line.append(")")
            i += 1
            continue

        # 逗号：换行（在 SELECT 列表、GROUP BY 等中，但函数调用内不换行）
        if token.type == "punctuation" and token.value == ",":
            current_line.append(",")
            if func_paren_depth == 0:
                flush_line()
            i += 1
            continue

        # 检查是否为顶层子句（需要换行）
        if token.type == "keyword":
            # 组合关键字（GROUP BY, ORDER BY, INNER JOIN 等）
            combined = token.value.upper()
            j = i + 1
            # 跳过空白
            while j < len(tokens) and tokens[j].type == "whitespace":
                j += 1
            if j < len(tokens) and tokens[j].type == "keyword":
                test_combined = combined + " " + tokens[j].value.upper()
                if test_combined in TOP_LEVEL_CLAUSES or test_combined in JOIN_CLAUSES:
                    combined = test_combined
                    i = j  # 跳过第二个关键字

            if combined in TOP_LEVEL_CLAUSES or combined in JOIN_CLAUSES:
                flush_line()
                # 管理列列表缩进
                if combined in ("FROM", "WHERE", "HAVING", "LIMIT", "OFFSET"):
                    list_indent = 0
                current_line.append(combined)
                # SELECT/GROUP BY/ORDER BY 关键字单独成行，列在下一行
                if combined in ("SELECT", "GROUP BY", "ORDER BY"):
                    flush_line()
                    list_indent = 1
                # ON 子句跟在 JOIN 后面
                i += 1
                continue

            # AND / OR：在 WHERE 中换行
            if combined in ("AND", "OR") and current_line:
                flush_line()
                current_line.append(combined)
                i += 1
                continue

        # 普通 token
        if token.type == "keyword":
            current_line.append(token.value.upper())
        else:
            current_line.append(token.value)

        i += 1

    flush_line()

    # 清理多余空行
    result = []
    prev_empty = False
    for line in lines:
        if line.strip() == "":
            if not prev_empty:
                result.append("")
            prev_empty = True
        else:
            result.append(line)
            prev_empty = False

    return "\n".join(result).strip() + "\n"


# ============================================================
# SQL 语法校验
# ============================================================

def check_sql(sql: str, dialect: str = "generic") -> Dict:
    """校验 SQL 语法"""
    errors = []
    warnings = []
    suggestions = []

    # 去除注释
    sql_no_comments = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_no_comments, flags=re.DOTALL)

    # 1. 括号匹配
    paren_stack = []
    for i, ch in enumerate(sql_no_comments):
        if ch == "(":
            paren_stack.append(i)
        elif ch == ")":
            if not paren_stack:
                errors.append(f"位置 {i}：多余的右括号 ')'")
            else:
                paren_stack.pop()
    if paren_stack:
        errors.append(f"位置 {paren_stack[-1]}：未闭合的左括号 '('")

    # 2. 引号匹配
    quote_count = sql_no_comments.count("'")
    if quote_count % 2 != 0:
        errors.append("单引号未闭合（奇数个单引号）")

    # 3. 关键字检查
    sql_upper = sql_no_comments.upper()

    # 检查 SELECT 是否存在
    if "SELECT" in sql_upper and "FROM" not in sql_upper:
        # 可能是 SELECT 常量，只警告
        if not re.search(r"SELECT\s+[\d'\"]", sql_upper, re.IGNORECASE):
            warnings.append("SELECT 语句缺少 FROM 子句")

    # 检查 SELECT *
    if re.search(r"SELECT\s+\*", sql_no_comments, re.IGNORECASE):
        warnings.append("使用了 SELECT *，建议在生产环境明确指定列名")

    # 检查 WHERE 1=1
    if re.search(r"WHERE\s+1\s*=\s*1", sql_no_comments, re.IGNORECASE):
        warnings.append("使用了 WHERE 1=1，确认是否为动态 SQL 拼接")

    # 检查没有 WHERE 的 DELETE/UPDATE
    if re.search(r"^(DELETE\s+FROM|UPDATE)\s+\w+", sql_no_comments, re.IGNORECASE | re.MULTILINE):
        if "WHERE" not in sql_upper:
            warnings.append("DELETE/UPDATE 语句没有 WHERE 条件，可能影响全部数据")

    # 检查 ORDER BY 缺少 ASC/DESC
    if "ORDER BY" in sql_upper:
        order_match = re.search(r"ORDER\s+BY\s+(.+?)(LIMIT|;|$)", sql_no_comments,
                                 re.IGNORECASE | re.DOTALL)
        if order_match:
            order_cols = order_match.group(1)
            if "ASC" not in order_cols.upper() and "DESC" not in order_cols.upper():
                suggestions.append("ORDER BY 未指定 ASC/DESC，默认 ASC，建议显式指定")

    # 4. 分号检查
    if sql_no_comments.strip() and not sql_no_comments.strip().endswith(";"):
        suggestions.append("建议在 SQL 语句末尾添加分号 ';'")

    # 5. 表别名建议
    if "JOIN" in sql_upper:
        from_match = re.search(r"FROM\s+(\w+)(\s+(?!JOIN|ON|WHERE|GROUP|ORDER|HAVING|LIMIT)\w+)?",
                                sql_no_comments, re.IGNORECASE)
        if from_match and not from_match.group(2):
            suggestions.append("多表查询建议为表添加别名以提高可读性")

    return {
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "passed": len(errors) == 0,
    }


def format_check_report(result: Dict) -> str:
    """格式化校验报告"""
    lines = []
    lines.append("📋 SQL 语法校验报告")
    lines.append("━" * 40)

    if result["errors"]:
        lines.append("❌ 错误：")
        for e in result["errors"]:
            lines.append(f"   - {e}")
    else:
        lines.append("✅ 括号匹配：通过")
        lines.append("✅ 引号匹配：通过")
        lines.append("✅ 关键字检查：通过")

    if result["warnings"]:
        lines.append("")
        lines.append("⚠️  警告：")
        for w in result["warnings"]:
            lines.append(f"   - {w}")

    if result["suggestions"]:
        lines.append("")
        lines.append("💡 建议：")
        for s in result["suggestions"]:
            lines.append(f"   - {s}")

    lines.append("")
    lines.append("━" * 40)
    status = "通过" if result["passed"] else "未通过"
    lines.append(f"结果：{status}（{len(result['errors'])} 个错误，"
                 f"{len(result['warnings'])} 个警告，{len(result['suggestions'])} 条建议）")

    return "\n".join(lines)


# ============================================================
# 表和列提取
# ============================================================

def extract_tables_columns(sql: str) -> Dict:
    """提取 SQL 中的表和列"""
    sql_no_comments = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_no_comments, flags=re.DOTALL)
    sql_upper = sql_no_comments.upper()

    tables = {}  # name -> alias
    columns = set()
    joins = []
    where_conditions = []

    # 提取 FROM 子句中的表
    from_pattern = r"FROM\s+([\w`\"']+)(?:\s+(?:AS\s+)?([\w`\"']+))?"
    for match in re.finditer(from_pattern, sql_no_comments, re.IGNORECASE):
        table_name = match.group(1).strip("`\"'")
        alias = match.group(2)
        if alias and alias.upper() not in ("WHERE", "GROUP", "ORDER", "HAVING",
                                             "LIMIT", "JOIN", "ON", "INNER", "LEFT",
                                             "RIGHT", "FULL", "CROSS", "UNION"):
            tables[table_name] = alias.strip("`\"'")
        else:
            tables[table_name] = None

    # 提取 JOIN 中的表
    join_pattern = r"(?:INNER|LEFT|RIGHT|FULL|CROSS|NATURAL)?\s*JOIN\s+([\w`\"']+)(?:\s+(?:AS\s+)?([\w`\"']+))?"
    for match in re.finditer(join_pattern, sql_no_comments, re.IGNORECASE):
        table_name = match.group(1).strip("`\"'")
        alias = match.group(2)
        if alias and alias.upper() not in ("ON", "USING", "WHERE"):
            tables[table_name] = alias.strip("`\"'")
        elif table_name not in tables:
            tables[table_name] = None

    # 提取 JOIN ON 条件
    on_pattern = r"JOIN\s+[\w`\"']+\s+(?:AS\s+)?[\w`\"']*\s*ON\s+([\w.]+)\s*=\s*([\w.]+)"
    for match in re.finditer(on_pattern, sql_no_comments, re.IGNORECASE):
        joins.append(f"{match.group(1)} = {match.group(2)}")

    # 提取 SELECT 列
    select_match = re.search(r"SELECT\s+(.+?)\s+FROM\s", sql_no_comments,
                              re.IGNORECASE | re.DOTALL)
    if select_match:
        select_cols = select_match.group(1)
        if "*" not in select_cols:
            for col in re.split(r",(?![^()]*\))", select_cols):
                col = col.strip()
                if col:
                    # 去除 AS 别名
                    col = re.sub(r"\s+AS\s+\w+$", "", col, flags=re.IGNORECASE).strip()
                    columns.add(col)

    # 提取 WHERE 条件
    where_match = re.search(r"WHERE\s+(.+?)(?:GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|;|$)",
                            sql_no_comments, re.IGNORECASE | re.DOTALL)
    if where_match:
        where_text = where_match.group(1).strip()
        # 按 AND/OR 分割
        conditions = re.split(r"\s+(?:AND|OR)\s+", where_text, flags=re.IGNORECASE)
        for cond in conditions:
            cond = cond.strip().rstrip(")")
            if cond:
                where_conditions.append(cond)

    # 提取 GROUP BY 列
    group_match = re.search(r"GROUP\s+BY\s+(.+?)(?:HAVING|ORDER\s+BY|LIMIT|;|$)",
                             sql_no_comments, re.IGNORECASE | re.DOTALL)
    group_cols = []
    if group_match:
        for col in group_match.group(1).split(","):
            col = col.strip()
            if col:
                group_cols.append(col)

    # 提取 ORDER BY 列
    order_match = re.search(r"ORDER\s+BY\s+(.+?)(?:LIMIT|;|$)",
                            sql_no_comments, re.IGNORECASE | re.DOTALL)
    order_cols = []
    if order_match:
        for col in order_match.group(1).split(","):
            col = col.strip()
            if col:
                order_cols.append(col)

    return {
        "tables": tables,
        "columns": sorted(columns),
        "joins": joins,
        "where_conditions": where_conditions,
        "group_by": group_cols,
        "order_by": order_cols,
    }


def format_extract_report(result: Dict) -> str:
    """格式化提取报告"""
    lines = []
    lines.append("📊 查询分析")
    lines.append("━" * 40)

    lines.append(f"涉及表（{len(result['tables'])}个）：")
    for i, (table, alias) in enumerate(result["tables"].items(), 1):
        alias_str = f" (别名 {alias})" if alias else ""
        lines.append(f"  {i}. {table}{alias_str}")

    if result["columns"]:
        lines.append("")
        lines.append(f"涉及列（{len(result['columns'])}个）：")
        for col in result["columns"]:
            lines.append(f"  - {col}")

    if result["joins"]:
        lines.append("")
        lines.append("JOIN 关系：")
        for join in result["joins"]:
            lines.append(f"  - {join}")

    if result["where_conditions"]:
        lines.append("")
        lines.append("WHERE 条件：")
        for cond in result["where_conditions"]:
            lines.append(f"  - {cond}")

    if result["group_by"]:
        lines.append("")
        lines.append(f"GROUP BY（{len(result['group_by'])}个字段）：")
        for col in result["group_by"]:
            lines.append(f"  - {col}")

    if result["order_by"]:
        lines.append("")
        lines.append(f"ORDER BY（{len(result['order_by'])}个字段）：")
        for col in result["order_by"]:
            lines.append(f"  - {col}")

    lines.append("")
    lines.append("━" * 40)
    return "\n".join(lines)


# ============================================================
# 查询结构解释
# ============================================================

def explain_sql(sql: str) -> Dict:
    """解释 SQL 查询结构"""
    sql_no_comments = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_no_comments, flags=re.DOTALL)
    sql_upper = sql_no_comments.upper()

    clauses = []

    # 检测各子句
    if "WITH" in sql_upper and re.search(r"^\s*WITH\s", sql_no_comments, re.IGNORECASE):
        clauses.append(("WITH", "定义公共表表达式（CTE）"))

    if re.search(r"SELECT\s", sql_upper):
        select_match = re.search(r"SELECT\s+(.+?)\s+FROM\s", sql_no_comments,
                                  re.IGNORECASE | re.DOTALL)
        if select_match:
            cols_text = select_match.group(1)
            col_count = len([c for c in cols_text.split(",") if c.strip()])
            has_agg = any(agg in sql_upper for agg in ("COUNT(", "SUM(", "AVG(", "MIN(", "MAX("))
            desc = f"选择 {col_count} 个字段"
            if has_agg:
                desc += "，包含聚合函数"
            if "DISTINCT" in sql_upper:
                desc += "，去重"
            clauses.append(("SELECT", desc))

    if "FROM" in sql_upper:
        from_match = re.search(r"FROM\s+([\w`\"']+)", sql_no_comments, re.IGNORECASE)
        if from_match:
            table = from_match.group(1).strip("`\"'")
            join_count = len(re.findall(r"\bJOIN\b", sql_upper))
            desc = f"从 {table} 表查询"
            if join_count > 0:
                desc += f"，连接 {join_count} 个表"
            clauses.append(("FROM/JOIN", desc))

    if "WHERE" in sql_upper:
        where_match = re.search(r"WHERE\s+(.+?)(?:GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|;|$)",
                                sql_no_comments, re.IGNORECASE | re.DOTALL)
        if where_match:
            cond_count = len(re.split(r"\s+(?:AND|OR)\s+", where_match.group(1).strip()))
            clauses.append(("WHERE", f"筛选 {cond_count} 个条件"))

    if "GROUP BY" in sql_upper:
        group_match = re.search(r"GROUP\s+BY\s+(.+?)(?:HAVING|ORDER\s+BY|LIMIT|;|$)",
                                 sql_no_comments, re.IGNORECASE | re.DOTALL)
        if group_match:
            col_count = len([c for c in group_match.group(1).split(",") if c.strip()])
            clauses.append(("GROUP BY", f"按 {col_count} 个字段分组"))

    if "HAVING" in sql_upper:
        clauses.append(("HAVING", "筛选分组结果"))

    if "ORDER BY" in sql_upper:
        order_match = re.search(r"ORDER\s+BY\s+(.+?)(?:LIMIT|;|$)",
                                 sql_no_comments, re.IGNORECASE | re.DOTALL)
        if order_match:
            col_count = len([c for c in order_match.group(1).split(",") if c.strip()])
            desc_text = order_match.group(1).upper()
            direction = "降序" if "DESC" in desc_text else "升序"
            clauses.append(("ORDER BY", f"按 {col_count} 个字段{direction}排序"))

    if "LIMIT" in sql_upper:
        limit_match = re.search(r"LIMIT\s+(\d+)", sql_no_comments, re.IGNORECASE)
        if limit_match:
            clauses.append(("LIMIT", f"取前 {limit_match.group(1)} 条"))

    # 执行顺序
    exec_order = []
    clause_order = ["WITH", "FROM/JOIN", "WHERE", "GROUP BY", "HAVING",
                    "SELECT", "ORDER BY", "LIMIT"]
    clause_dict = dict(clauses)
    for name in clause_order:
        if name in clause_dict:
            exec_order.append((name, clause_dict[name]))

    return {
        "clauses": clauses,
        "exec_order": exec_order,
    }


def format_explain_report(result: Dict) -> str:
    """格式化解释报告"""
    lines = []
    lines.append("🔍 查询结构解释")
    lines.append("━" * 40)

    lines.append("执行顺序：")
    for i, (name, desc) in enumerate(result["exec_order"], 1):
        lines.append(f"  {i}. {name}：{desc}")

    lines.append("")
    lines.append("子句分析：")
    for name, desc in result["clauses"]:
        lines.append(f"  - {name}：{desc}")

    lines.append("")
    lines.append("━" * 40)
    return "\n".join(lines)


# ============================================================
# 压缩 SQL
# ============================================================

def minify_sql(sql: str) -> str:
    """压缩 SQL 为单行"""
    # 去除注释
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    # 合并空白
    sql = re.sub(r'\s+', ' ', sql)
    # 去除逗号后空格前的多余空格（保留逗号后一个空格）
    sql = re.sub(r'\s*,\s*', ', ', sql)
    # 去除括号内外多余空格
    sql = re.sub(r'\s*\(\s*', '(', sql)
    sql = re.sub(r'\s*\)\s*', ')', sql)
    return sql.strip()


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="SQL 格式化与分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", "-f", default="", help="SQL 文件路径")
    parser.add_argument("--sql", "-s", default="", help="直接输入 SQL 语句")
    parser.add_argument("--dialect", "-d", default="generic",
                        choices=list(DIALECTS), help="SQL 方言（默认 generic）")
    parser.add_argument("--indent", type=int, default=4, help="缩进空格数（默认 4）")
    parser.add_argument("--check", action="store_true", help="语法校验")
    parser.add_argument("--extract", action="store_true", help="提取表和列")
    parser.add_argument("--explain", action="store_true", help="解释查询结构")
    parser.add_argument("--minify", action="store_true", help="压缩输出")
    parser.add_argument("--all", action="store_true", help="全部功能（格式化+校验+提取+解释）")
    parser.add_argument("--output", "-o", metavar="FILE", help="输出到文件")
    args = parser.parse_args()

    # 读取 SQL
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                sql = f.read()
        except (OSError, IOError) as e:
            print(f"错误：无法读取文件 {args.file}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.sql:
        sql = args.sql
    else:
        print("错误：请通过 --file 或 --sql 提供 SQL 输入", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if not sql.strip():
        print("错误：SQL 内容为空", file=sys.stderr)
        sys.exit(1)

    output_parts = []

    # 格式化（默认或 --all）
    if not (args.check or args.extract or args.explain or args.minify) or args.all:
        if args.minify:
            formatted = minify_sql(sql)
        else:
            formatted = format_sql(sql, indent=args.indent, dialect=args.dialect)
        output_parts.append(formatted)

    # 压缩
    if args.minify and not args.all:
        output_parts.append(minify_sql(sql))

    # 校验
    if args.check or args.all:
        result = check_sql(sql, dialect=args.dialect)
        output_parts.append(format_check_report(result))

    # 提取
    if args.extract or args.all:
        result = extract_tables_columns(sql)
        output_parts.append(format_extract_report(result))

    # 解释
    if args.explain or args.all:
        result = explain_sql(sql)
        output_parts.append(format_explain_report(result))

    # 合并输出
    output = "\n\n".join(output_parts)

    print(output)

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output + "\n")
            print(f"\n已保存到：{args.output}", file=sys.stderr)
        except (OSError, IOError) as e:
            print(f"错误：无法写入文件 {args.output}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
