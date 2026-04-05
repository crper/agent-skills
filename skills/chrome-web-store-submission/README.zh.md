# Chrome Web Store Submission

[English](./README.md) | 简体中文

为浏览器扩展准备可直接复制粘贴的 Chrome Web Store 提交信息，包括政策字段、权限理由、隐私 / 数据使用说明、Reviewer Note 和商店文案。

## 适用范围

- 适合**上架文案与审核字段填写**
- 支持**单语**或**中英双语**输出
- 输出结构稳定，方便直接复制粘贴

## 目录结构

- `scripts/inspect_extension_facts.py`：扩展事实检查脚本
- `SKILL.md`：技能说明和工作流
- `references/field-templates.md`：字段模板与稳定输出顺序
- `references/permission-patterns.md`：权限字段措辞模式
- `agents/openai.yaml`：Agent UI 预设提示
- `evals/evals.json`：后续回归检查可复用的最小评测提示集

## 适合处理的任务

- 填写 Chrome Web Store 发布表单
- 编写单一用途说明
- 解释权限申请原因
- 回答远程代码问题
- 编写数据使用与隐私披露
- 生成短描述和详细介绍

## 输出风格

这个技能可以输出：

- 仅中文
- 仅英文
- 中英双语

默认稳定字段顺序：

1. 单一用途说明
2. 实际申请到的权限理由（按稳定顺序输出）
3. 远程代码
4. 数据使用
5. 商店文案
6. Reviewer Note

## 说明

- 这个技能会先检查当前扩展代码，再生成内容
- 只会为扩展**实际声明的权限**生成理由，不会补写未申请的权限字段
- 它只负责**可复制粘贴的提交文案**，不负责自动发布
- 优先使用准确、审核友好的表述，而不是宣传式文案
