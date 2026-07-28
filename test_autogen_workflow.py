import asyncio

from autogen_core import AgentId, SingleThreadedAgentRuntime

from agents.autogen_machine_agent import AutoGenMachineAgent
from agents.quality_agent import QualityAgent
from agents.maintenance_agent import MaintenanceAgent
from agents.coordinator_agent import CoordinatorAgent

from messages.order_message import OrderMessage


async def main() -> None:
    runtime = SingleThreadedAgentRuntime()

    # Register Machine Agent M01
    await AutoGenMachineAgent.register(
        runtime,
        "machine_agent",
        lambda: AutoGenMachineAgent(
            machine_id="M01",
            status="available",
            capability="milling",
            queue_length=2,
            estimated_processing_time_mins=45,
            maintenance_condition=0.85,
            active_warnings=["minor_vibration"],
        ),
    )

    # Register Quality Agent
    await QualityAgent.register(
        runtime,
        "quality_agent",
        lambda: QualityAgent(),
    )

    # Register Maintenance Agent
    await MaintenanceAgent.register(
        runtime,
        "maintenance_agent",
        lambda: MaintenanceAgent(),
    )

    # Register Coordinator Agent
    await CoordinatorAgent.register(
        runtime,
        "coordinator_agent",
        lambda: CoordinatorAgent(),
    )

    runtime.start()

    order = OrderMessage(
        order_id="ORD-001",
        priority="High",
        required_capability="milling",
        deadline_minutes=120,
        quality_requirement="Strict",
    )

    print("\nSTARTING COMPLETE AUTOGEN WORKFLOW\n")

    final_response = await runtime.send_message(
        order,
        recipient=AgentId(
            "coordinator_agent",
            "default",
        ),
    )

    print("\nFINAL AUTOGEN RECOMMENDATION")

    if final_response is None:
        print("The Coordinator did not return a response.")
    else:
        print(final_response.model_dump_json(indent=4))

    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())