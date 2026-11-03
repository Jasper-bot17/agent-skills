# gitignore-generator 示例

## 示例 1：Node.js 前端项目

```bash
python3 gen_gitignore.py --type node,common
```

生成的 .gitignore 包含：
- node_modules/
- dist/, build/, .next/
- .env, .env.local
- .DS_Store, Thumbs.db
- .vscode/, .idea/

## 示例 2：Python 数据科学项目

```bash
python3 gen_gitignore.py --type python,common
```

生成的 .gitignore 包含：
- __pycache__/
- venv/, .venv/
- *.egg-info/
- .pytest_cache/, .coverage
- .ipynb_checkpoints/
- OS 和编辑器文件

## 示例 3：C++ 项目

```bash
python3 gen_gitignore.py --type cpp,common
```

生成的 .gitignore 包含：
- build/, bin/, obj/
- *.o, *.exe, *.out
- CMakeCache.txt, CMakeFiles/
- .vs/

## 示例 4：全栈项目（Node + Python）

```bash
python3 gen_gitignore.py --type node,python,common,web
```

组合生成前后端通用的忽略规则。

## 示例 5：预览模式

```bash
# 先看看会生成什么，不写入文件
python3 gen_gitignore.py --type go --preview
```

## 示例 6：交互式选择

```bash
python3 gen_gitignore.py --interactive
# 输入编号组合选择项目类型
```
