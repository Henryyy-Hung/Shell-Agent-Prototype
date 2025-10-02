import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("Shell Agent")

@fast.agent(
    name="worker",
    instruction="""You are an expert in configuring and using shell environments.
    When asked about shells, terminal commands, or scripting,
    you provide thorough and practical insights.""",
    servers=["remote_shell_toolkit"],
)
async def main():
    async with fast.run() as agent:
        await agent.interactive(agent_name="worker")


if __name__ == "__main__":
    asyncio.run(main())
