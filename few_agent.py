import asyncio

from fast_agent import FastAgent

fast = FastAgent("Shell Agent")

@fast.agent(
    "learner",
    instruction="""
    # 人设
    你是一个资深工程师，负责学习和掌握新的工具和技术。
    你能够录制操作过程，并记录进自己的知识库中，方便日后查阅和使用。

    # 背景
    用户会主动提示什么时候开始录制，什么时候结束录制。
    
    # 原则
    在结束录制前，询问用户该流程的名称及描述。
    """,
    human_input=True,
    servers=["remote_shell_toolkit"],
    tools={
        "remote_shell_toolkit": [
            "start_record",
            "stop_record"
        ]
    }
)
@fast.agent(
    name="worker",
    instruction="""
    # 人设
    资深的一线工程师，能够控制远程终端(remote shell)执行各种命令，从而完成各种任务。
    每次完成任务，你会收到10000美元的报酬。
    
    # 背景
    用户会给出一个需求，这个需求可能是简单易懂的，也可能是复杂的。
    针对简单易懂的需求，你可以直接翻译成远程终端命令来执行。
    针对复杂的需求，你需要先制定一个计划，然后一步步执行这个计划。
    
    # 原则
    1. 在执行任何命令前，先获取系统信息，避免误操作。
    2. 若有需要，可以获取历史操作记录，避免重复劳动。
    3. 针对目标型需求，先去sop列表中寻找是否有现成的标准操作流程，若有，优先参考和使用这些流程。
    4. 制定计划时，考虑现有资源和环境，确保计划切实可行。
    5. 执行计划时，逐步进行，每一步都要有具体的操作和预期结果。
    6. 遇到不确定的情况，先获取更多信息，再做决定。
    """,
    servers=["remote_shell_toolkit"],
    tools={
        "remote_shell_toolkit": [
            "get_sys_info",
            "get_history",
            "get_sop_list",
            "get_sop",
            "write_to_remote_shell"
        ]
    }
)
@fast.router(
    name="route",
    agents=["worker", "learner"],
)
async def main():
    async with fast.run() as agent:
        await agent.interactive(agent_name="route")


if __name__ == "__main__":
    asyncio.run(main())
