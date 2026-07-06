# 新增 Agent 准备工作提示词模板

```text
请在 D:\桌面文件下载\AI-hermes-agent\agents\<NEW-AGENT-NAME> 目录下，为一个新 agent 完成“可开始开发前”的准备工作。目标是让这个新 agent 可以在当前目录内独立开发、运行和测试，同时继续共享上层 D:\桌面文件下载\AI-hermes-agent 的 shared、.env、公共配置和基础服务。不要改无关 agent 的业务代码，除非是为了注册当前新 agent 或补充共享配置字段。

请按下面步骤执行：

1. 先检查当前目录是否已经有代码、README、pyproject.toml、api、service、workflow、tests、main.py、Dockerfile；如果只有 README 或为空，就按仓库现有 agent 风格脚手架化。
2. 复用上层仓库能力，确保新 agent 默认接入：
   - shared.agent_runtime
   - shared.schemas
   - shared.config
   - shared.logger
   - shared.registry
   - 根目录 .env
3. 为当前 agent 搭建最小可运行结构，至少包含：
   - bootstrap.py
   - main.py
   - pyproject.toml
   - Dockerfile
   - api/app.py
   - service/executor.py
   - workflow/
   - tests/
   - README.md 中的本地开发说明
4. 让这个 agent 在当前目录内支持：
   - `python main.py`
   - `pytest`
   - 共享上层 `.env`
   - 共享上层 `shared/*`
5. 如果当前 agent 有明确业务目标，就在当前目录中补齐“准备工作文档”，例如：
   - docs/integration-checklist.md
   - docs/data-contract.md
   - docs/runtime-notes.md
   - docs/todo.md
6. 根据该 agent 的业务目标，定义最小数据契约和执行流：
   - 输入 schema
   - 输出 schema
   - 核心 task 名称
   - workflow 主入口
   - 外部依赖点
7. 如果需要新增该 agent 专属环境变量：
   - 优先补充到上层 shared/config/settings.py
   - 命名遵循大写前缀规范
   - 只增加和当前 agent 直接相关的字段
8. 把该 agent 注册到 shared/registry/service.py，但不要修改其他 agent 的业务逻辑。
9. 加最小测试覆盖，至少验证：
   - app 能启动
   - `/health` 正常
   - `/execute` 正常
   - 至少一个核心业务路由或核心 workflow 能返回预期结构
10. 如果项目里仍有 stub、假实现、待接真实 API 的地方，请直接整理成当前目录内可见的待办清单或文档，不要只在回复里口头说明。

执行原则：
- 只围绕当前新 agent 目录工作
- 默认复用上层仓库基础设施，不要拆成完全独立系统
- 优先参考现有 agent 的目录结构和编码方式
- 能直接落文件就直接落文件，不只给建议
- 不要为了省事跳过测试
- 不要动无关 agent，除非是共享配置或注册项
- 如果发现当前目录已有一部分实现，基于现状补齐，不要粗暴重写

完成后请输出：
1. 已补齐的准备工作
2. 新增或修改了哪些关键文件
3. 当前 agent 还缺哪些外部信息
4. 下一步最适合继续开发的入口文件
5. 本地验证是否通过，包括具体执行了什么命令
```
