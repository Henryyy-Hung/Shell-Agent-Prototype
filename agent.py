import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("fast-agent example")


# Define the agent
@fast.agent(
    name="shell_expert",
    instruction="""You are an expert in configuring and using shell environments.
    When asked about shells, terminal commands, or scripting,
    you provide thorough and practical insights.""",
    servers=["remote-shell"],
)
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive(agent_name="shell_expert")


if __name__ == "__main__":
    asyncio.run(main())
