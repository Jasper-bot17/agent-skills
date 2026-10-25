# Base64 速查指南

> base64-tool 技能配套指南。

---

## 一、什么是 Base64

Base64 是一种用 64 个可打印 ASCII 字符表示二进制数据的编码方式。每 3 字节（24 位）数据被编码为 4 个 Base64 字符。

**编码后体积增大约 33%**：3 字节 → 4 字符。

---

## 二、字符集

| 范围 | 字符 |
|---|---|
| A-Z | 大写字母（0-25） |
| a-z | 小写字母（26-51） |
| 0-9 | 数字（52-61） |
| + / | 标准 Base64 的最后两个（62, 63） |
| - _ | URL-safe Base64 的最后两个 |
| = | Padding 填充（补齐到 4 的倍数） |

---

## 三、标准 vs URL-safe

| 特性 | 标准 Base64 | URL-safe Base64 |
|---|---|---|
| 第 62 字符 | `+` | `-` |
| 第 63 字符 | `/` | `_` |
| Padding | `=`（可能出现） | 通常省略 |
| 适用场景 | 文件、Data URL | URL 参数、JWT、文件名 |

---

## 四、常见用途

### 1. Data URL（内嵌图片）

```
data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...
```

适合小图标、头像；不适合大图（HTML 会膨胀）。

### 2. HTTP Basic Auth

```
Authorization: Basic dXNlcjE6cGFzc3dvcmQ=
# 解码后: user1:password
```

### 3. JWT Token

JWT 的 Header 和 Payload 部分使用 URL-safe Base64 编码。

### 4. 配置文件中的二进制

将证书、密钥等二进制文件转为 Base64 文本，方便放入 YAML/JSON 配置。

---

## 五、快速命令

```bash
# 编码
echo -n "Hello" | base64
# 解码
echo "SGVsbG8=" | base64 -d

# URL-safe
echo -n "Hello" | base64 | tr '+/' '-_' | tr -d '='

# 文件转 Base64
base64 image.png

# Base64 还原文件
echo "iVBORw..." | base64 -d > image.png
```

---

## 六、注意事项

1. **Base64 不是加密**：它只是编码，任何人都可以解码
2. **UTF-8 中文**：中文每字 3 字节，Base64 编码后更长
3. **Padding**：当原始字节数不是 3 的倍数时，用 `=` 补齐
4. **换行**：某些 Base64 实现每 76 字符换行（MIME 格式），解码前需去除
5. **大文件**：Base64 不适合传输大文件，应使用二进制传输

---

*本指南由 base64-tool 技能提供*
