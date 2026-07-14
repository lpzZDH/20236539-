# Conversation doc_summary_long

- memory_id: `mem_conversation_doc_summary_long`
- conversation_id: `doc_summary_long`
- created_or_updated_at: `2026-07-06T01:58:24`

## Final Answer

B5 Memory Module - Advanced Features

B5是本地memory管理模块，负责读取memory配置和memory_index.json，根据用户指定的memory_id与全局记忆配置选择记忆文档，并返回给B1。同时能够将当前对话的messages、trace、final_answer保存为对话记忆或全局记忆。

基础功能：
1. Memory查找流程：读取memory.yaml → 根据selected_memory_ids查找指定记忆 → 如果use_global_memory=true则加载全局记忆 → 按max_memory_chars截断 → 写入selected_memory.json并返回给B1
2. Memory保存流程：读取memory_save_input.json或接收B1传入路径 → 读取messages/trace/final_answer → 生成memory_id、title、summary → 保存为Markdown记忆文档 → 更新memory_index.json → 写入saved_memory.json与memory_log.jsonl

进阶功能：
- 关键词检索排序，返回Top-K个memory文档
- 自动将较长messages/answer压缩为总结摘要（调用B4 LLM进行智能摘要生成）
- 对指定memory文档进行更新，对比新旧文档内容，对重复、补充或冲突信息进行合并、修正或冲突管理
- 向量检索，返回相似度最高的Top-K个memory文档
- 分析错误memory对最终回答的影响，评估记忆可靠性分数

错误记忆：内容错误或过时的memory，可能误导LLM生成错误回答。需要检测并评估其对最终回答的影响程度。

## Messages

```json
[{"role": "system", "content": "You are a helpful agent."}, {"role": "user", "content": "什么是Agent系统？"}, {"role": "assistant", "content": "Agent系统是一种能够自主理解目标、调用工具并完成任务的智能系统。"}]
```

## Trace

```json
{
  "turns": 1,
  "tool_calls": 0,
  "llm_calls": 1,
  "status": "success"
}
```
