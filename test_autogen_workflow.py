import asyncio

from autogen_core import AgentId, SingleThreadedAgentRuntime

from agents.autogen_machine_agent import AutoGenMachineAgent
from agents.quality_agent import QualityAgent
from agents.maintenance_agent import MaintenanceAgent
from agents.coordinator_agent import CoordinatorAgent

from messages.order_message import OrderMessage


async def main() -> None:
    # Create the AutoGen runtime
    runtime = SingleThreadedAgentRuntime()

    # -------------------------------------------------
    # Register Machine M01
    # Correct capability and acceptable condition
    # -------------------------------------------------
    machine_m01 = AutoGenMachineAgent(
        machine_id="M01",
        status="available",
        capability="milling",
        queue_length=2,
        estimated_processing_time_mins=45,
        maintenance_condition=0.85,
        active_warnings=["minor_vibration"],
    )

    await machine_m01.register_instance(
        runtime,
        AgentId("machine_agent", "M01"),
    )

    # -------------------------------------------------
    # Register Machine M02
    # Available, but has the wrong capability
    # -------------------------------------------------
    machine_m02 = AutoGenMachineAgent(
        machine_id="M02",
        status="available",
        capability="turning",
        queue_length=1,
        estimated_processing_time_mins=30,
        maintenance_condition=0.90,
        active_warnings=[],
    )

    await machine_m02.register_instance(
        runtime,
        AgentId("machine_agent", "M02"),
    )

    # -------------------------------------------------
    # Register Machine M03
    # Correct capability, but has a critical fault
    # -------------------------------------------------
    machine_m03 = AutoGenMachineAgent(
        machine_id="M03",
        status="available",
        capability="milling",
        queue_length=0,
        estimated_processing_time_mins=25,
        maintenance_condition=0.40,
        active_warnings=["critical_fault"],
    )

    await machine_m03.register_instance(
        runtime,
        AgentId("machine_agent", "M03"),
    )

    # -------------------------------------------------
    # Register the Quality Agent
    # -------------------------------------------------
    await QualityAgent.register(
        runtime,
        "quality_agent",
        lambda: QualityAgent(),
    )

    # -------------------------------------------------
    # Register the Maintenance Agent
    # -------------------------------------------------
    await MaintenanceAgent.register(
        runtime,
        "maintenance_agent",
        lambda: MaintenanceAgent(),
    )

    # -------------------------------------------------
    # Register the Coordinator Agent
    # -------------------------------------------------
    await CoordinatorAgent.register(
        runtime,
        "coordinator_agent",
        lambda: CoordinatorAgent(),
    )

    # Start the AutoGen runtime
    runtime.start()

    # -------------------------------------------------
    # Create the manufacturing order
    # -------------------------------------------------
    order = OrderMessage(
        order_id="ORD-001",
        priority="High",
        required_capability="milling",
        deadline_minutes=120,
        quality_requirement="Strict",
    )

    print("\nSTARTING COMPLETE MULTI-MACHINE AUTOGEN WORKFLOW\n")

    # Send the order to the Coordinator
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

    # Stop when all messages have been processed
    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())