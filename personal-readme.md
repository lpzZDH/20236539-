# B5 Memory Module Proposal

## 1. 基本信息

| 项目 | 内容 |
|------|------|
| 姓名 | 刘沛泽 |
| 学号 | 20236539 |
| 小组名称 / 项目名称 | Agent 智能体开发团队 |
| 选择的模块名称 | B5 记忆文档存储与查找模块 |
| 合并的系统名称 | 本地 Agent 智能体系统（Local Agent System） |

---

## 2. 项目整体背景与个人模块定位

### 2.1 项目整体目标

本项目面向本地工具调用型 Agent 智能体开发场景，基于 **Qwen3.5-4B** 本地大语言模型，采用 **ReAct** 框架思想，构建一个能够在本地环境自主运行、调用工具、利用历史记忆完成用户任务的 Agent 系统。

整体系统包括：
- **B1**: Agent 运行与消息管理
- **B2**: Skill 工具函数
- **B3**: 说明生成与工具调用
- **B4**: LLM 决策
- **B5**: 记忆文档存储与查找

最终实现从用户输入到工具调用再到记忆保存的完整闭环。

### 2.2 个人模块在整体系统中的定位

B5 模块属于 Agent 系统的**记忆管理层**，位于数据持久化层。它负责读取、查找和保存 memory 文档，提供接口给 B1 使用。B1 会把 B5 返回的记忆文本注入 messages，供 LLM 决策使用。

文档分为两种类型：
- **全局记忆**: 跨任务共享
- **对话记忆**: 单次任务

**该模块接收以下输入:**
- `memory.yaml`: 记忆系统配置文件
- `selected_memory_ids`: 用户指定的记忆文档 ID 列表
- `use_global_memory`: 是否加载全局记忆
- 保存时的 messages、trace、final_answer

**该模块输出以下结果:**
- `selected_memory.json`: 返回给 B1 的记忆内容
- `saved_memory.json`: 保存后的 memory 元信息
- `memory_index.json`: 记忆索引文件
- Markdown 格式的记忆文档(存放于 `memory/conversations/` 或 `memory/global/`)

该模块为系统提供了**记忆注入**和**记忆持久化**两项核心能力，使 Agent 能够利用历史信息做出更准确的决策。

---

## 3. 模块要解决的具体问题

本模块主要解决 Agent 系统中历史信息的有效存储、索引和检索问题。由于 Agent 系统需要多轮交互，LLM 本身是无状态的，如果不将历史对话和全局知识持久化存储，每次任务都需要从零开始，无法利用过往经验。因此，本模块需要实现一个轻量级的本地记忆管理系统。

### 原始问题中的具体难点

| 难点 | 说明 |
|------|------|
| **记忆长度管理** | LLM 上下文窗口有限(通常为 4096 tokens)，过长的记忆会挤占有效输入空间，需要实现智能截断 |
| **记忆类型区分** | 全局记忆(跨任务共享)与对话记忆(单次任务)的使用场景和生命周期不同，需要不同的存储结构 |
| **索引一致性** | `memory_index.json` 需要与实际文件系统保持同步，防止索引与实际文件不一致 |
| **记忆质量风险** | 错误或过时的记忆可能误导 LLM 生成错误回答 |

如果没有该模块，Agent 系统将处于**无状态运行**，无法获取历史上下文和全局知识，也无法追溯和复盘过往对话。

### 预期目标

- 支持按 `memory_id` 精确查找记忆文档(延迟 < 100ms)
- 支持全局记忆与对话记忆的分类存储
- 记忆返回长度可控(默认上限 2000 字符)
- 保存操作自动生成元数据并同步更新索引

---

## 4. 技术方案与实现路径

### 4.1 技术选型

| 类型 | 名称 | 用途 | 选择原因 |
|------|------|------|----------|
| 编程语言 | Python 3.10 | 模块实现 | 与团队技术栈一致 |
| 框架/库 | PyYAML | 解析 YAML 配置文件 | 标准库支持，轻量可靠 |
| 模型/算法 | 确定性文本规则 | 生成 title 和 summary | 基础版不调用 LLM，降低依赖 |
| 数据库/存储 | 本地文件系统 | 存储记忆文档和索引 | 简单可靠，无需额外依赖 |
| 文档格式 | Markdown | 记忆文档存储格式 | 人类可读，支持丰富格式 |
| 索引格式 | JSON | `memory_index.json` | 程序友好，解析快速 |
| 日志格式 | JSON Lines | 操作日志记录 | 追加写入友好 |

### 4.2 模块流程设计

#### Memory 查找流程

![图 2: Memory 查找流程图](images/flow_retrieval.png)

1. 读取 `memory.yaml` 配置文件
2. 根据 `selected_memory_ids` 在 `memory_index.json` 中查找对应文档路径
3. 若 `use_global_memory=true`，加载 `memory/global/` 目录下的全局记忆
4. 按 `max_memory_chars` 截断超长内容
5. 写入 `selected_memory.json` 并返回给 B1

#### Memory 保存流程

![图 3: Memory 保存流程图](images/flow_save.png)

1. 接收 `conversation_id`、messages、trace、final_answer
2. 生成 `memory_id`、title 和 summary
3. 构建 Markdown 记忆文档并写入文件
4. 更新 `memory_index.json` 索引
5. 写入 `saved_memory.json` 和 `memory_log.jsonl`

### 4.3 具体实施方法设计

#### 核心数据结构

**(1) `memory.yaml` 配置结构:**

```yaml
memory:
  root_dir: ../memory
  global_memory_dir: global
  conversation_memory_dir: conversations
  index_path: memory_index.json
  max_memory_chars: 2000
```

**(2) `memory_index.json` 索引结构:**

```json
{
  "memories": [
    {
      "memory_id": "mem_conversation_conv_001",
      "type": "conversation",
      "title": "Agent 工具调用总结",
      "path": "conversations/mem_conversation_conv_001.md",
      "created_at": "2026-06-24T20:52:00"
    }
  ]
}
```

#### 核心函数设计

**(1) 记忆查找函数:**

```python
def load_memory(config, select_memory_ids, use_global_memory, query=None):
    """Load memory documents by memory_id and global config"""
    memories = []
    total_chars = 0
    max_chars = config['memory']['max_memory_chars']

    for mem_id in select_memory_ids:
        mem_path = _resolve_memory_path(config, mem_id)
        content = _read_memory_file(mem_path)
        memories.append({"id": mem_id, "content": content})
        total_chars += len(content)

    if use_global_memory:
        global_mems = _load_global_memories(config)
        for gm in global_mems:
            if total_chars + len(gm['content']) > max_chars:
                gm['content'] = gm['content'][:max_chars - total_chars]
                gm['truncated'] = True
            memories.append(gm)
            total_chars += len(gm['content'])

    combined = _merge_memories(memories)
    truncated = len(combined) > max_chars
    if truncated:
        combined = combined[:max_chars]

    return {
        "memories": memories,
        "combined_content": combined,
        "total_chars": len(combined),
        "max_chars": max_chars,
        "truncated": truncated
    }
```

**(2) 记忆保存函数:**

```python
def save_memory(config, conversation_id, save_type,
                messages, trace, final_answer):
    """Save current conversation as memory document and update index"""
    memory_id = f"mem_{save_type}_{conversation_id}"
    title = _generate_title(messages)
    summary = _generate_summary(final_answer)

    doc = _build_memory_document(
        memory_id=memory_id, save_type=save_type,
        title=title, summary=summary,
        conversation_id=conversation_id,
        messages=messages, trace=trace,
        final_answer=final_answer
    )

    file_path = _get_memory_file_path(config, save_type, memory_id)
    _write_markdown(file_path, doc)
    _update_memory_index(config, memory_id, save_type, title, file_path)

    return memory_id
```

#### 接口定义

| 接口 | 输入 | 输出 | 调用方 |
|------|------|------|--------|
| `load_memory()` | config, memory_ids[], use_global, query | `selected_memory.json` | B1 Runtime |
| `save_memory()` | config, conv_id, save_type, messages, trace, answer | `saved_memory.json` | B1 Runtime |

#### 异常处理

| 异常场景 | 处理策略 |
|----------|----------|
| memory_id 不存在 | 记录 warning，跳过该记忆，继续处理其他 |
| 记忆内容超过长度限制 | 按顺序截断，标记 `truncated=true` |
| 索引文件损坏 | 自动重建空索引，记录 error 日志 |
| 目标目录不存在 | 自动创建目录 |
| memory_id 已存在 | 覆盖旧文件，更新索引时间戳 |

---

## 5. 与其他模块的连接和融合方式

![图 4: B5 与其他模块的连接关系](images/module_connection.png)

B5 模块**仅与 B1(Agent 运行与消息管理模块)直接交互**，不与其他模块发生直接调用关系。

B1 在 Agent Loop 开始前调用 `B5.load_memory()` 获取记忆上下文，在对话结束后根据 `save_memory` 参数调用 `B5.save_memory()` 保存本轮记忆。

连接方式为 **Python 函数调用**。B1 将 `memory_config` 和相关参数传递给 B5，B5 返回结构化字典。数据交换格式为 Python 字典(内部调用)和 JSON 文件(调试输出)。

输入输出字段已统一：B5 返回的 `combined_content` 为字符串类型，直接拼入 messages；B1 传入的 `save_type` 取值为 `"conversation"`、`"global"` 或 `"none"`。错误处理采用防御式策略，查找错误在返回值中记录，保存错误由 B1 捕获记录到 trace。

---

## 6. 实验计划

### 6.1 计划运行环境

| 项目 | 配置 |
|------|------|
| 操作系统 | Ubuntu 22.04 LTS |
| Python 版本 | 3.10 |
| 主要依赖 | PyYAML |
| 硬件环境 | CPU 服务器，16GB+ 内存，SSD 存储 |

### 6.2 测试数据或输入样例

**测试场景一(记忆查找):**

```bash
python b5_memory.py \
  --config ../configs/memory.yaml \
  --select_memory_ids mem_conversation_conv_000 \
  --use_global_memory true \
  --query "Agent 系统如何调用工具?" \
  --outdir ../outputs/B5_memory
```

**测试场景二(记忆保存):**

```json
// memory_save_input.json
{
  "conversation_id": "conv_sample_001",
  "save_type": "conversation",
  "messages_path": "sample_messages.json",
  "trace_path": "sample_trace.json",
  "answer_path": "sample_final_answer.md"
}
```

```bash
python b5_memory.py \
  --config ../configs/memory.yaml \
  --save_type conversation \
  --save_input_path ../data/memory_inputs/memory_save_input.json \
  --outdir ../outputs/B5_memory
```

---

## 7. 图片插入与提交要求

本文档中的图片均为本地图片，已存放在与文档同级的 `images/` 目录下。

![图 1: B5 模块在 Agent 系统中的位置](images/system_architecture.png)

| 图片文件名 | 说明 |
|-----------|------|
| `images/system_architecture.png` | 图 1: B5 模块在 Agent 系统中的位置 |
| `images/flow_retrieval.png` | 图 2: Memory 查找流程图 |
| `images/flow_save.png` | 图 3: Memory 保存流程图 |
| `images/module_connection.png` | 图 4: B5 与其他模块的连接关系 |

提交时请将文档文件与 `images/` 文件夹一并提交，确保图片路径使用相对路径。

---

## 8. 参考文献

1. Yao S, Zhao J, Yu D, et al. **ReAct: Synergizing Reasoning and Acting in Language Models**. ICLR, 2023.
2. Packer V, Fang V, Patil SG, et al. **MemGPT: Towards LLMs as Operating Systems**. arXiv preprint, 2023.
3. Qwen Team. **Qwen3.5 Technical Report**. Alibaba Cloud, 2025.
