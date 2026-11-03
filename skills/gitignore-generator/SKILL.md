---
name: gitignore-generator
description: ".gitignore 生成器。根据项目类型（Node/Python/Java/C++/Go/Rust 等）自动生成标准 .gitignore 文件，支持组合多种项目类型，自动包含 OS 文件、编辑器配置、依赖目录、构建产物等常见忽略项。"
---

# .gitignore 生成器

根据项目技术栈自动生成完整的 `.gitignore` 文件。

## 触发场景

- 新建项目时不知道该忽略哪些文件
- 项目包含多种技术栈，需要合并多套忽略规则
- 提交了 `node_modules/`、`__pycache__/`、`.env` 等不该提交的文件后补救
- 需要为不同语言/框架生成标准忽略模板

## 支持的项目类型

| 类型 | 参数 | 典型内容 |
|---|---|---|
| Node.js | `node` | node_modules, dist, .env, npm/yarn 日志 |
| Python | `python` | __pycache__, venv, *.egg-info, .pytest_cache |
| Java | `java` | target, *.class, .idea, *.jar |
| C/C++ | `cpp` | build/, *.o, *.exe, *.out, .vs |
| Go | `go` | vendor/, *.test, coverage.out |
| Rust | `rust` | target/, Cargo.lock（按需） |
| Web | `web` | node_modules, dist, build, .next, .nuxt |
| 通用 | `common` | .DS_Store, Thumbs.db, .vscode/.idea, *.log |

## 使用方法

```bash
# 基本用法（在项目目录下运行）
python3 gen_gitignore.py --type node

# 组合多种类型
python3 gen_gitignore.py --type node,python

# 指定输出路径
python3 gen_gitignore.py --type cpp --output .gitignore

# 预览不写入
python3 gen_gitignore.py --type java --preview

# 交互式选择
python3 gen_gitignore.py --interactive
```

## 操作步骤

1. 确定项目使用的技术栈
2. 运行 `gen_gitignore.py --type <类型>`
3. 检查生成的 `.gitignore` 是否满足需求
4. 如有自定义忽略项，手动追加

## 注意事项

- 已存在 `.gitignore` 时会自动备份为 `.gitignore.bak`
- `--type` 可逗号分隔多个类型，脚本会去重合并
- 常用 `common` 类型建议始终加上，覆盖 OS 和编辑器文件
