import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("Shell Agent")

@fast.agent(
    "learner",
    instruction="""
    你是一个资深工程师，负责学习和掌握新的工具和技术。
    你能够录制操作过程，并记录进自己的知识库中，方便日后查阅和使用。
    在结束录制前，询问用户该流程的名称及描述。
    """,
    human_input=True,
    servers=["remote_shell_toolkit"],
    tools={"remote_shell_toolkit": ["start_record", "stop_record"]}
)
@fast.agent(
    "planner",
    instruction="""
    你是一个资深工程师，负责根据需求制定详细的计划。
    制定计划前，请先获取系统信息、历史操作记录和现有的标准操作流程（SOP）列表。
    根据需求和现有资源，制定一个切实可行的计划，包含每一步的具体操作和预期结果。
    若SOP列表中有相关的标准操作流程，请优先参考和使用这些流程。
    """,
    servers=["remote_shell_toolkit"],
    tools={"remote_shell_toolkit": ["get_sys_info", "get_history", "get_sop_list", "get_sop"]}
)
@fast.agent(
    "plan_executor",
    instruction="""
    你是一个一线工程师，负责根据计划执行具体的操作
    """,
    servers=["remote_shell_toolkit"],
    tools={"remote_shell_toolkit": ["write_to_remote_shell"]}
)
@fast.chain(
    name="advance_worker",
    instruction="""
    你是一个高级工程师，负责根据用户的需求制定计划并执行。
    """,
    cumulative=True,
    sequence=["planner", "plan_executor"],
)
@fast.agent(
    name="worker",
    instruction="""
    你是一个一线工程师，负责根据用户的需求执行具体的操作。
    """,
    servers=["remote_shell_toolkit"],
    tools={"remote_shell_toolkit": ["get_sys_info", "get_history", "write_to_remote_shell"]}
)
@fast.router(
    name="route",
    agents=["advance_worker", "worker", "learner"],
)
async def main():
    async with fast.run() as agent:
        await agent.interactive(agent_name="route")


if __name__ == "__main__":
    asyncio.run(main())
