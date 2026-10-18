# citation-gate

**中文** | [English](#english)

**引用闸**：LLM 的结论必须能回指你发给它的真实记录，对不上的一律丢弃。

```bash
pip install citation-gate
```

```python
from citation_gate import verify_claims

records = [{"id": 1, "text": "明天三点开会"}, {"id": 2, "text": "报价已发"}]  # 你发给模型的数据
claims = model_output["facts"]  # 每条带 text + ids/message_ids

kept, rejected = verify_claims(claims, records)
# kept[0]["evidence"] == [{"id": 1, "quote": "明天三点开会"}] — 直接可渲染
```

## 方法论

让 LLM 总结你的私有数据，它一定会产出流利的编造。对策是**结构性校验**，不是更好的提示词：

1. 发给模型的每条记录都带编号
2. 要求每个结论引用编号（message_ids）
3. 校验时只认**本次发送集合内的编号**——模型"记得"的不算
4. 无引用、引用解析失败、文本为空的结论 → 丢弃并计数
5. 幸存结论自动附上证据（id + 原文摘录），渲染时所见即所据

一条无法指回证据的结论，与幻觉无法区分——所以它不配被存储、不配被展示。

## 为什么

提示词约束（"请引用来源"）只能降低概率，闸门把它变成确定性。抽取自生产级功能（Trace 的 AI 档案：模型产出 JSON facts，逐条对消息 ID 校验后才入库）。

## 测试

```bash
python -m unittest discover tests
```

MIT — Brook Zeng

---

<a name="english"></a>

# citation-gate (English)

**Citation gate**: every LLM claim must trace back to records you actually sent it — anything that doesn't resolve gets dropped.

```bash
pip install citation-gate
```

```python
from citation_gate import verify_claims

records = [{"id": 1, "text": "meeting at 3pm"}, {"id": 2, "text": "quote sent"}]  # what you sent
claims = model_output["facts"]  # each with text + ids/message_ids

kept, rejected = verify_claims(claims, records)
# kept[0]["evidence"] == [{"id": 1, "quote": "meeting at 3pm"}] — ready to render
```

## The method

An LLM summarizing your private data will invent fluent conclusions. The counter is **structural verification**, not better prompting:

1. Give every record you send an id
2. Require every claim to cite ids (`message_ids`)
3. Accept only ids **from the exact set you sent** — what the model "remembers" doesn't count
4. Claims with no citation, unresolvable citations, or empty text → dropped and counted
5. Surviving claims gain an evidence list (id + quoted source) — what you render is what it's based on

A conclusion that cannot point back at evidence is indistinguishable from a hallucination — so it never gets stored or shown.

## Why

Prompt constraints ("please cite sources") only lower the probability; a gate makes it deterministic. Extracted from a production feature (Trace's AI dossier: the model emits JSON facts, each verified against message ids before storage).

## Test

```bash
python -m unittest discover tests
```

MIT — Brook Zeng
