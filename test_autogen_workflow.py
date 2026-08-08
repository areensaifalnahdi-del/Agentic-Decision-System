import asyncio
import random
import json

from agents.order_agent import OrderAgent
from autogen_core import AgentId, SingleThreadedAgentRuntime

from agents.autogen_machine_agent import AutoGenMachineAgent
from agents.quality_agent import QualityAgent
from agents.maintenance_agent import MaintenanceAgent
from agents.coordinator_agent import CoordinatorAgent

from colorama import Fore, Style, init

init(autoreset=True)


async def main() -> None:
    # Create the AutoGen runtime
    runtime = SingleThreadedAgentRuntime()

    # -------------------------------------------------
    # Register 10 Machine Agents
    # -------------------------------------------------

    machine_m01 = AutoGenMachineAgent(
        machine_id="M01",
        status="available",
        capability="milling",
        queue_length=2,
        estimated_processing_time_mins=45,
        maintenance_condition=0.85,
        active_warnings=[],
    )

    machine_m01.status = random.choice(["available", "busy", "maintenance"])
    machine_m01.queue_length = random.randint(0, 5)
    machine_m01.estimated_processing_time_mins = random.randint(20, 90)
    machine_m01.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m01.maintenance_condition < 0.5:
        machine_m01.active_warnings = ["critical_fault"]
    elif machine_m01.maintenance_condition < 0.8:
        machine_m01.active_warnings = ["minor_vibration"]
    else:
        machine_m01.active_warnings = []

    await machine_m01.register_instance(
        runtime,
        AgentId("machine_agent", "M01")
    )

    machine_m02 = AutoGenMachineAgent(
        machine_id="M02",
        status="available",
        capability="turning",
        queue_length=1,
        estimated_processing_time_mins=30,
        maintenance_condition=0.90,
        active_warnings=[],
    )

    machine_m02.status = random.choice(["available", "busy", "maintenance"])
    machine_m02.queue_length = random.randint(0, 5)
    machine_m02.estimated_processing_time_mins = random.randint(20, 90)
    machine_m02.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m02.maintenance_condition < 0.5:
        machine_m02.active_warnings = ["critical_fault"]
    elif machine_m02.maintenance_condition < 0.8:
        machine_m02.active_warnings = ["minor_vibration"]
    else:
        machine_m02.active_warnings = []

    await machine_m02.register_instance(
        runtime,
        AgentId("machine_agent", "M02")
    )

    machine_m03 = AutoGenMachineAgent(
        machine_id="M03",
        status="available",
        capability="milling",
        queue_length=0,
        estimated_processing_time_mins=25,
        maintenance_condition=0.40,
        active_warnings=[],
    )

    machine_m03.status = random.choice(["available", "busy", "maintenance"])
    machine_m03.queue_length = random.randint(0, 5)
    machine_m03.estimated_processing_time_mins = random.randint(20, 90)
    machine_m03.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m03.maintenance_condition < 0.5:
        machine_m03.active_warnings = ["critical_fault"]
    elif machine_m03.maintenance_condition < 0.8:
        machine_m03.active_warnings = ["minor_vibration"]
    else:
        machine_m03.active_warnings = []

    await machine_m03.register_instance(
        runtime,
        AgentId("machine_agent", "M03")
    )

    machine_m04 = AutoGenMachineAgent(
        machine_id="M04",
        status="available",
        capability="milling",
        queue_length=3,
        estimated_processing_time_mins=60,
        maintenance_condition=0.95,
        active_warnings=[],
    )

    machine_m04.status = random.choice(["available", "busy", "maintenance"])
    machine_m04.queue_length = random.randint(0, 5)
    machine_m04.estimated_processing_time_mins = random.randint(20, 90)
    machine_m04.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m04.maintenance_condition < 0.5:
        machine_m04.active_warnings = ["critical_fault"]
    elif machine_m04.maintenance_condition < 0.8:
        machine_m04.active_warnings = ["minor_vibration"]
    else:
        machine_m04.active_warnings = []

    await machine_m04.register_instance(
        runtime,
        AgentId("machine_agent", "M04")
    )

    machine_m05 = AutoGenMachineAgent(
        machine_id="M05",
        status="busy",
        capability="milling",
        queue_length=5,
        estimated_processing_time_mins=90,
        maintenance_condition=0.88,
        active_warnings=[],
    )

    machine_m05.status = random.choice(["available", "busy", "maintenance"])
    machine_m05.queue_length = random.randint(0, 5)
    machine_m05.estimated_processing_time_mins = random.randint(20, 90)
    machine_m05.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m05.maintenance_condition < 0.5:
        machine_m05.active_warnings = ["critical_fault"]
    elif machine_m05.maintenance_condition < 0.8:
        machine_m05.active_warnings = ["minor_vibration"]
    else:
        machine_m05.active_warnings = []

    await machine_m05.register_instance(
        runtime,
        AgentId("machine_agent", "M05")
    )

    machine_m06 = AutoGenMachineAgent(
        machine_id="M06",
        status="available",
        capability="drilling",
        queue_length=2,
        estimated_processing_time_mins=35,
        maintenance_condition=0.93,
        active_warnings=[],
    )

    machine_m06.status = random.choice(["available", "busy", "maintenance"])
    machine_m06.queue_length = random.randint(0, 5)
    machine_m06.estimated_processing_time_mins = random.randint(20, 90)
    machine_m06.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m06.maintenance_condition < 0.5:
        machine_m06.active_warnings = ["critical_fault"]
    elif machine_m06.maintenance_condition < 0.8:
        machine_m06.active_warnings = ["minor_vibration"]
    else:
        machine_m06.active_warnings = []

    await machine_m06.register_instance(
        runtime,
        AgentId("machine_agent", "M06")
    )

    machine_m07 = AutoGenMachineAgent(
        machine_id="M07",
        status="available",
        capability="milling",
        queue_length=1,
        estimated_processing_time_mins=40,
        maintenance_condition=0.80,
        active_warnings=[],
    )

    machine_m07.status = random.choice(["available", "busy", "maintenance"])
    machine_m07.queue_length = random.randint(0, 5)
    machine_m07.estimated_processing_time_mins = random.randint(20, 90)
    machine_m07.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m07.maintenance_condition < 0.5:
        machine_m07.active_warnings = ["critical_fault"]
    elif machine_m07.maintenance_condition < 0.8:
        machine_m07.active_warnings = ["minor_vibration"]
    else:
        machine_m07.active_warnings = []

    await machine_m07.register_instance(
        runtime,
        AgentId("machine_agent", "M07")
    )

    machine_m08 = AutoGenMachineAgent(
        machine_id="M08",
        status="maintenance",
        capability="milling",
        queue_length=0,
        estimated_processing_time_mins=0,
        maintenance_condition=0.30,
        active_warnings=[],
    )

    machine_m08.status = random.choice(["available", "busy", "maintenance"])
    machine_m08.queue_length = random.randint(0, 5)
    machine_m08.estimated_processing_time_mins = random.randint(20, 90)
    machine_m08.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m08.maintenance_condition < 0.5:
        machine_m08.active_warnings = ["critical_fault"]
    elif machine_m08.maintenance_condition < 0.8:
        machine_m08.active_warnings = ["minor_vibration"]
    else:
        machine_m08.active_warnings = []

    await machine_m08.register_instance(
        runtime,
        AgentId("machine_agent", "M08")
    )

    machine_m09 = AutoGenMachineAgent(
        machine_id="M09",
        status="available",
        capability="turning",
        queue_length=4,
        estimated_processing_time_mins=55,
        maintenance_condition=0.91,
        active_warnings=[],
    )

    machine_m09.status = random.choice(["available", "busy", "maintenance"])
    machine_m09.queue_length = random.randint(0, 5)
    machine_m09.estimated_processing_time_mins = random.randint(20, 90)
    machine_m09.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m09.maintenance_condition < 0.5:
        machine_m09.active_warnings = ["critical_fault"]
    elif machine_m09.maintenance_condition < 0.8:
        machine_m09.active_warnings = ["minor_vibration"]
    else:
        machine_m09.active_warnings = []

    await machine_m09.register_instance(
        runtime,
        AgentId("machine_agent", "M09")
    )

    machine_m10 = AutoGenMachineAgent(
        machine_id="M10",
        status="available",
        capability="milling",
        queue_length=2,
        estimated_processing_time_mins=50,
        maintenance_condition=0.97,
        active_warnings=[],
    )

    machine_m10.status = random.choice(["available", "busy", "maintenance"])
    machine_m10.queue_length = random.randint(0, 5)
    machine_m10.estimated_processing_time_mins = random.randint(20, 90)
    machine_m10.maintenance_condition = round(random.uniform(0.3, 1.0), 2)

    if machine_m10.maintenance_condition < 0.5:
        machine_m10.active_warnings = ["critical_fault"]
    elif machine_m10.maintenance_condition < 0.8:
        machine_m10.active_warnings = ["minor_vibration"]
    else:
        machine_m10.active_warnings = []

    await machine_m10.register_instance(
        runtime,
        AgentId("machine_agent", "M10")
    )

    # -------------------------------------------------
    # Register specialist and coordinator agents
    # -------------------------------------------------

    await QualityAgent.register(
        runtime,
        "quality_agent",
        lambda: QualityAgent(),
    )

    await MaintenanceAgent.register(
        runtime,
        "maintenance_agent",
        lambda: MaintenanceAgent(),
    )

    await CoordinatorAgent.register(
        runtime,
        "coordinator_agent",
        lambda: CoordinatorAgent(),
    )

    # Start the AutoGen runtime
    runtime.start()

    order_agent = OrderAgent()

    print()
    print(
        Fore.CYAN
        + Style.BRIGHT
        + "STARTING COMPLETE MULTI-MACHINE AUTOGEN WORKFLOW"
    )
    print()

    while True:
        order = order_agent.generate_random_order()

        final_response = await runtime.send_message(
            order,
            recipient=AgentId(
                "coordinator_agent",
                "default",
            ),
        )

        # -------------------------------------------------
        # Final recommendation
        # -------------------------------------------------

        print()
        print(
            Fore.CYAN
            + Style.BRIGHT
            + "=========================================="
        )
        print(
            Fore.CYAN
            + Style.BRIGHT
            + "        FINAL AUTOGEN RECOMMENDATION"
        )
        print(
            Fore.CYAN
            + Style.BRIGHT
            + "=========================================="
        )

        if final_response is None:
            print(
                Fore.RED
                + "The Coordinator did not return a response."
            )

        else:
            print()

            print(
                Fore.BLUE
                + "Order ID:"
                + Style.RESET_ALL,
                final_response.order_id,
            )

            if final_response.selected_machine == "none":
                print(
                    Fore.RED
                    + "Selected Machine:"
                    + Style.RESET_ALL,
                    final_response.selected_machine,
                )
            else:
                print(
                    Fore.GREEN
                    + Style.BRIGHT
                    + "Selected Machine:"
                    + Style.RESET_ALL,
                    Style.BRIGHT
                    + final_response.selected_machine,
                )

            print(
                Fore.YELLOW
                + "Justification:"
                + Style.RESET_ALL,
                final_response.justification,
            )

            print()
            print(
                Fore.MAGENTA
                + Style.BRIGHT
                + "Required Actions:"
            )

            for action, value in final_response.required_actions.items():
                print(
                    "  "
                    + Fore.YELLOW
                    + action
                    + Style.RESET_ALL
                    + ": "
                    + str(value)
                )

            print()
            print(
                Fore.RED
                + Style.BRIGHT
                + "Rejected Machines:"
            )

            if final_response.machines_filtered_out:
                for machine in final_response.machines_filtered_out:
                    print(
                        "  "
                        + Fore.RED
                        + machine["machine_id"]
                        + Style.RESET_ALL
                        + " -> "
                        + machine["reason"]
                    )
            else:
                print(
                    "  "
                    + Fore.GREEN
                    + "None"
                    + Style.RESET_ALL
                )

            print()
            print(
                Fore.CYAN
                + Style.BRIGHT
                + "Evidence:"
            )

            evidence = final_response.evidence

            print()

            # Order evidence
            if "order" in evidence:
                order_evidence = evidence["order"]

                print(
                    Fore.BLUE
                    + Style.BRIGHT
                    + "  Order:"
                    + Style.RESET_ALL
                )

                print(
                    f"    Order ID: {order_evidence.get('order_id')}"
                )

                print(
                    f"    Required Capability: "
                    f"{order_evidence.get('required_capability')}"
                )

                print(
                    f"    Quality Requirement: "
                    f"{order_evidence.get('quality_requirement')}"
                )

                print(
                    f"    Deadline: "
                    f"{order_evidence.get('deadline_minutes')} minutes"
                )

            # Selected machine evidence
            if evidence.get("selected_machine"):
                machine = evidence["selected_machine"]

                print()
                print(
                    Fore.GREEN
                    + Style.BRIGHT
                    + "  Selected Machine Evidence:"
                    + Style.RESET_ALL
                )

                print(
                    f"    Machine ID: {machine.get('machine_id')}"
                )

                print(
                    f"    Status: {machine.get('status')}"
                )

                print(
                    f"    Capability: {machine.get('capability')}"
                )

                print(
                    f"    Queue Length: {machine.get('queue_length')}"
                )

                print(
                    f"    Processing Time: "
                    f"{machine.get('estimated_processing_time_mins')} mins"
                )

                print(
                    f"    Maintenance Condition: "
                    f"{machine.get('maintenance_condition')}"
                )

                print(
                    f"    Warnings: "
                    f"{', '.join(machine.get('active_warnings', [])) or 'None'}"
                )

                quality = machine.get("quality_assessment")

                if quality:
                    print(
                        f"    Quality Risk: "
                        f"{quality.get('quality_risk_score')}"
                    )

                    print(
                        f"    Quality Action: "
                        f"{quality.get('recommended_action')}"
                    )

                maintenance = machine.get("maintenance_assessment")

                if maintenance:
                    print(
                        f"    Maintenance Status: "
                        f"{maintenance.get('availability_status')}"
                    )
                    print(
                        f"    Maintenance Action: "
                        f"{maintenance.get('maintenance_action_required')}"
                    )

            else:
                print()
                print(
                    Fore.RED
                    + Style.BRIGHT
                    + "  Selected Machine Evidence:"
                    + Style.RESET_ALL
                    + " None"
                )

            # Rejected machines evidence
            rejected = evidence.get("rejected_machines", [])

            print()
            print(
                Fore.RED
                + Style.BRIGHT
                + "  Rejected Machine Evidence:"
                + Style.RESET_ALL
            )

            if rejected:
                for machine in rejected:
                    print(
                        f"    {machine.get('machine_id')}: "
                        f"{machine.get('reason')}"
                    )
            else:
                print("    None")

        print()
        print(
            Fore.CYAN
            + Style.BRIGHT
            + "=========================================="
        )

        print()
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
