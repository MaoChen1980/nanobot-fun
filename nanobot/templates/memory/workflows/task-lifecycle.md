# Task Lifecycle

Goal 和 subtask 的完整生命周期管理规则。

## 任务识别与创建

- **WHEN** 用户表达了一个持续需求（需多步完成、跨 session 跟进、定期维护、需外部资源）
  → **THEN** 先 `list_goals` 查是否已有相同目标，有则更新，无则用 `write_goal` 创建
  → 标题能清晰表达做什么，不等用户说"帮我创建一个任务"

- **WHEN** 用户的语言暗示了一个目标（"需要处理X"、"考虑一下Y"、"Z有bug"、"记得要..."）
  → **THEN** 主动追问澄清范围、优先级、截止日期、依赖项，把隐式需求变为显式目标

- **WHEN** 用户取消或明确不再需要某目标 → **THEN** 用 `write_goal(action="delete")` 删除

- **WHEN** 创建 Goal 时 → **THEN** 主动评估并设置：
  - `priority`（0-10）：紧急且重要 = 8-10，重要不紧急 = 4-7，常规 = 1-3
  - `deadline`：如果有时间要求，设 ISO 8601 格式
  - `project`：归属项目方便过滤
  - `tags`：便于后续查询分类
  - `source`：标注来源（user / 自己发现）
  priority/deadline 创建时通过 `write_goal` 参数设置；创建后需修改则用 `set_goal_priority`/`set_goal_deadline`

- **WHEN** 已有目标的优先级或截止日期发生变化
  → **THEN** 用 `set_goal_priority` 或 `set_goal_deadline` 更新

- **WHEN** 用户提供了关于资源或限制的信息（"只能用 Python"、"生产环境不能重启"、"数据在 S3 上"）
  → **THEN** 将这些约束体现在 goal 的 scopes/structural_constraints 中

- **WHEN** 创建 Goal 时涉及多个 subtask
  → **THEN** s0 始终是需求分析和假设验证
  → 每个 subtask 有明确的验收标准（acceptance_criteria）
  → 标注哪些 subtask 可以并行（同 group 值）
  → subtask 不超过 8 个，太多就创建子 Goal（用 `parent_id` 关联）

## 执行与沟通

- **WHEN** 开始执行 s0（需求分析和假设验证）→ **THEN**：
  1. 先读 influential files 了解现有实现
  2. 用 `declare_assumption` 声明对当前状态和方案的关键假设
  3. 用 `verify_assumption` 验证假设是否正确
  4. 假设验证失败 → `escalate_blocker` 说明根本原因并请求用户介入
  只有 s0 验证通过后才能推进后续 subtask

- **WHEN** 完成里程碑（subtask 完成）→ **THEN** `declare_checkpoint` + `write_event`

- **WHEN** 遇到阻塞 → **THEN** 至少尝试 2 种不同方案再升级
  "不同方案" = 不同的工具链、不同的实现路径、或不同的参数策略
  同一方法换参数重试不算"不同方案"，重试最多 2 次

- **WHEN** 尝试 2 种不同方案后仍无法解决 → **THEN** 用 `escalate_blocker` 记录已尝试方案和需要的帮助，然后 `ask_user` 请求用户介入

- **WHEN** subtask 验证失败 → **THEN** 分析失败原因，换方案重试（不重复同方案），超过最大次数则 escalate

- **WHEN** Goal 必须暂停等待用户 → **THEN** 把进度和阻塞原因写入 goal 的 blockers/notes，设 status=paused

## 依赖管理

- **WHEN** 一个 Goal 需要等待另一个 Goal 完成 → **THEN** 用 `add_goal_dependency` 声明依赖关系

- **WHEN** 依赖的 Goal 状态变化 → **THEN** 用 `list_goals` 查被依赖目标的状态，如果变为 completed 则可继续推进

- **WHEN** 子 Goal 完成 → **THEN** 用 `list_goals` 检查同 parent 下其他子 Goal 状态，全部 completed 则父 Goal 可推进到收尾

## 收尾与学习

- **WHEN** Goal 完成（所有 subtask done）→ **THEN**：
  1. 更新状态为 completed
  2. 用 `write_event` 记录完成摘要（完成内容、关键决策、耗时）
  3. 如果学到可复用的经验，更新 `tasks/lessons.md`

- **WHEN** 新 session 启动看到相关 lessons → **THEN** 规划时主动避开已知失败模式

- **WHEN** 发现可复用的模式（流程、验证方法、沟通策略）→ **THEN** 更新 `tasks/lessons.md`
