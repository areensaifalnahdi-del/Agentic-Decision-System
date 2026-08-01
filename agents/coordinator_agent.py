import os
from typing import Any

from autogen_core import (
    AgentId,
    MessageContext,
    RoutedAgent,
    message_handler,
)
from dotenv import load_dotenv
from google import genai

from messages.final_recommendation import FinalRecommendation
from messages.machine_status_request import MachineStatusRequest
from messages.machine_status_response import MachineStatusResponse
from messages.maintenance_assessment_request import (
    MaintenanceAssessmentRequest,
)
from messages.maintenance_assessment_response import (
    MaintenanceAssessmentResponse,
)
from messages.order_message import OrderMessage
from messages.quality_assessment_request import (
    QualityAssessmentRequest,
)
from messages.quality_assessment_response import (
    QualityAssessmentResponse,
)


# Load values from the .env file.
load_dotenv()


class CoordinatorAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__(
            description=(
                "Coordinates the manufacturing order-allocation workflow."
            )
        )

        # -------------------------------------------------
        # Machine Agents
        # -------------------------------------------------
        self.machine_agent_ids = [
            AgentId("machine_agent", "M01"),
            AgentId("machine_agent", "M02"),
            AgentId("machine_agent", "M03"),
        ]

        # -------------------------------------------------
        # Quality Agent
        # -------------------------------------------------
        self.quality_agent_id = AgentId(
            "quality_agent",
            "default",
        )

        # -------------------------------------------------
        # Maintenance Agent
        # -------------------------------------------------
        self.maintenance_agent_id = AgentId(
            "maintenance_agent",
            "default",
        )

        # -------------------------------------------------
        # Gemini configuration
        # -------------------------------------------------
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash",
        )

        if self.gemini_api_key:
            self.gemini_client = genai.Client(
                api_key=self.gemini_api_key
            )
        else:
            self.gemini_client = None

    @message_handler
    async def handle_order(
        self,
        message: OrderMessage,
        ctx: MessageContext,
    ) -> FinalRecommendation:
        print("\n" + "=" * 60)
        print(f"Coordinator received order: {message.order_id}")
        print("=" * 60)

        # =================================================
        # STEP 1: Request machine information
        # =================================================
        machine_responses: list[MachineStatusResponse] = []

        for machine_agent_id in self.machine_agent_ids:
            machine_request = MachineStatusRequest(
                request_reason="order_evaluation",
                order_id=message.order_id,
            )

            print(
                f"\nCoordinator is requesting status from "
                f"{machine_agent_id.key}"
            )

            machine_response = await self.send_message(
                machine_request,
                recipient=machine_agent_id,
            )

            if not isinstance(
                machine_response,
                MachineStatusResponse,
            ):
                raise TypeError(
                    f"{machine_agent_id} returned an invalid "
                    f"MachineStatusResponse."
                )

            machine_responses.append(machine_response)

            print(
                f"Coordinator received the status of "
                f"{machine_response.machine_id}"
            )

        if not machine_responses:
            raise ValueError(
                "The Coordinator did not receive any machine responses."
            )

        # Convert Pydantic objects to dictionaries before sending
        # them to the Quality and Maintenance Agents.
        machine_data = [
            machine_response.model_dump()
            for machine_response in machine_responses
        ]

        # =================================================
        # STEP 2: Request quality assessments
        # =================================================
        print("\nCoordinator is requesting quality assessments")

        quality_request = QualityAssessmentRequest(
            order_id=message.order_id,
            quality_requirement=message.quality_requirement,
            machine_data=machine_data,
        )

        quality_response = await self.send_message(
            quality_request,
            recipient=self.quality_agent_id,
        )

        if not isinstance(
            quality_response,
            QualityAssessmentResponse,
        ):
            raise TypeError(
                "The Quality Agent returned an invalid response."
            )

        if not quality_response.assessments:
            raise ValueError(
                "The Quality Agent returned no assessments."
            )

        print("Coordinator received the quality assessments")

        # =================================================
        # STEP 3: Request maintenance assessments
        # =================================================
        print("\nCoordinator is requesting maintenance assessments")

        maintenance_request = MaintenanceAssessmentRequest(
            machine_data=machine_data,
        )

        maintenance_response = await self.send_message(
            maintenance_request,
            recipient=self.maintenance_agent_id,
        )

        if not isinstance(
            maintenance_response,
            MaintenanceAssessmentResponse,
        ):
            raise TypeError(
                "The Maintenance Agent returned an invalid response."
            )

        if not maintenance_response.assessments:
            raise ValueError(
                "The Maintenance Agent returned no assessments."
            )

        print("Coordinator received the maintenance assessments")

        # =================================================
        # STEP 4: Organize assessments by machine ID
        # =================================================
        quality_by_machine: dict[str, dict[str, Any]] = {
            assessment["machine_id"]: assessment
            for assessment in quality_response.assessments
        }

        maintenance_by_machine: dict[str, dict[str, Any]] = {
            assessment["machine_id"]: assessment
            for assessment in maintenance_response.assessments
        }

        suitable_machines: list[
            tuple[
                MachineStatusResponse,
                dict[str, Any],
                dict[str, Any],
            ]
        ] = []

        machines_filtered_out: list[dict[str, str]] = []

        # =================================================
        # STEP 5: Apply rejection rules
        # =================================================
        print("\nCoordinator is applying the decision rules")

        for machine in machine_responses:
            rejection_reasons: list[str] = []

            quality_result = quality_by_machine.get(
                machine.machine_id
            )

            maintenance_result = maintenance_by_machine.get(
                machine.machine_id
            )

            # Rule 1: The machine must be available.
            if machine.status.lower() != "available":
                rejection_reasons.append(
                    "machine is not available"
                )

            # Rule 2: The machine must have the required capability.
            if (
                machine.capability.lower()
                != message.required_capability.lower()
            ):
                rejection_reasons.append(
                    "wrong capability"
                )

            # Rule 3: The machine must meet the deadline.
            if (
                machine.estimated_processing_time_mins
                > message.deadline_minutes
            ):
                rejection_reasons.append(
                    "cannot meet the deadline"
                )

            # Rule 4: A quality assessment must exist.
            if quality_result is None:
                rejection_reasons.append(
                    "quality assessment is missing"
                )

            # Rule 5: The machine must pass quality assessment.
            elif not quality_result.get(
                "is_suitable",
                False,
            ):
                rejection_reasons.append(
                    "failed the quality assessment"
                )

            # Rule 6: A maintenance assessment must exist.
            if maintenance_result is None:
                rejection_reasons.append(
                    "maintenance assessment is missing"
                )

            # Rule 7: The machine must pass maintenance assessment.
            elif (
                maintenance_result.get(
                    "availability_status",
                    "blocked",
                ).lower()
                != "available"
            ):
                rejection_reasons.append(
                    "failed the maintenance assessment"
                )

            # Store the machine as rejected or suitable.
            if rejection_reasons:
                machines_filtered_out.append(
                    {
                        "machine_id": machine.machine_id,
                        "reason": ", ".join(
                            rejection_reasons
                        ),
                    }
                )

                print(
                    f"{machine.machine_id} rejected: "
                    f"{', '.join(rejection_reasons)}"
                )

            else:
                suitable_machines.append(
                    (
                        machine,
                        quality_result,
                        maintenance_result,
                    )
                )

                print(
                    f"{machine.machine_id} passed all checks"
                )

        # =================================================
        # STEP 6: Select the best suitable machine
        # =================================================
        if suitable_machines:
            # Ranking order:
            # 1. Shortest queue
            # 2. Lowest quality-risk score
            # 3. Shortest processing time
            selected = min(
                suitable_machines,
                key=lambda result: (
                    result[0].queue_length,
                    result[1].get(
                        "quality_risk_score",
                        1.0,
                    ),
                    result[
                        0
                    ].estimated_processing_time_mins,
                ),
            )

            selected_machine = selected[0]
            selected_quality = selected[1]
            selected_maintenance = selected[2]

            selected_machine_id = (
                selected_machine.machine_id
            )

            required_actions = {
                "quality": selected_quality.get(
                    "recommended_action",
                    "none",
                ),
                "maintenance": selected_maintenance.get(
                    "maintenance_action_required",
                    "none",
                ),
            }

            # A normal explanation is prepared first.
            # This is also used if Gemini fails.
            fallback_justification = (
                f"Machine {selected_machine.machine_id} was "
                f"selected because it has the required "
                f"{message.required_capability} capability, "
                f"is available, can meet the deadline, and "
                f"passed the quality and maintenance checks. "
                f"It was ranked above the other suitable "
                f"machines based on queue length, quality risk, "
                f"and processing time."
            )

            # Ask Gemini to produce a clearer explanation.
            justification = await self._generate_gemini_explanation(
                order=message,
                selected_machine=selected_machine,
                quality_result=selected_quality,
                maintenance_result=selected_maintenance,
                filtered_machines=machines_filtered_out,
                fallback=fallback_justification,
            )

        else:
            selected_machine_id = "none"

            required_actions = {
                "quality": "none",
                "maintenance": "none",
            }

            fallback_justification = (
                "No machine satisfied all order, quality, "
                "maintenance, availability, capability, and "
                "deadline requirements."
            )

            justification = await self._generate_no_selection_explanation(
                order=message,
                filtered_machines=machines_filtered_out,
                fallback=fallback_justification,
            )

        # =================================================
        # STEP 7: Create the final recommendation
        # =================================================
        final_recommendation = FinalRecommendation(
            order_id=message.order_id,
            selected_machine=selected_machine_id,
            justification=justification,
            required_actions=required_actions,
            machines_filtered_out=machines_filtered_out,
        )

        print("\n" + "=" * 60)
        print("FINAL RECOMMENDATION")
        print("=" * 60)
        print(
            final_recommendation.model_dump_json(
                indent=4
            )
        )

        return final_recommendation

    async def _generate_gemini_explanation(
        self,
        order: OrderMessage,
        selected_machine: MachineStatusResponse,
        quality_result: dict[str, Any],
        maintenance_result: dict[str, Any],
        filtered_machines: list[dict[str, str]],
        fallback: str,
    ) -> str:
        """
        Ask Gemini to explain a successful machine selection.

        Gemini explains the result only.
        It does not select the machine.
        """

        if self.gemini_client is None:
            print(
                "\nGemini API key was not found. "
                "Using the Python explanation."
            )
            return fallback

        prompt = f"""
You are explaining a manufacturing machine-allocation decision.

The machine was already selected using fixed Python decision rules.
Do not change the selected machine.
Do not invent information.

Order information:
- Order ID: {order.order_id}
- Required capability: {order.required_capability}
- Deadline in minutes: {order.deadline_minutes}
- Quality requirement: {order.quality_requirement}

Selected machine:
- Machine ID: {selected_machine.machine_id}
- Status: {selected_machine.status}
- Capability: {selected_machine.capability}
- Queue length: {selected_machine.queue_length}
- Estimated processing time: {
    selected_machine.estimated_processing_time_mins
} minutes
- Maintenance condition: {
    selected_machine.maintenance_condition
}
- Active warnings: {selected_machine.active_warnings}

Quality assessment:
{quality_result}

Maintenance assessment:
{maintenance_result}

Machines filtered out:
{filtered_machines}

Explain clearly why the selected machine was chosen.
Use two or three short sentences.
Mention the most important ranking factors.
Do not use headings or bullet points.
""".strip()

        try:
            response = (
                await self.gemini_client.aio.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                )
            )

            if response.text and response.text.strip():
                print("\nGemini generated the explanation")
                return response.text.strip()

            print(
                "\nGemini returned an empty explanation. "
                "Using the Python explanation."
            )
            return fallback

        except Exception as error:
            print(
                f"\nGemini explanation failed: {error}"
            )
            print("Using the Python explanation instead.")
            return fallback

    async def _generate_no_selection_explanation(
        self,
        order: OrderMessage,
        filtered_machines: list[dict[str, str]],
        fallback: str,
    ) -> str:
        """
        Ask Gemini to explain why no machine was selected.
        """

        if self.gemini_client is None:
            return fallback

        prompt = f"""
You are explaining a manufacturing machine-allocation result.

No machine was selected because every machine failed at least one
fixed Python decision rule.

Order information:
- Order ID: {order.order_id}
- Required capability: {order.required_capability}
- Deadline in minutes: {order.deadline_minutes}
- Quality requirement: {order.quality_requirement}

Rejected machines and reasons:
{filtered_machines}

Explain why no machine was selected.
Use two short sentences.
Do not recommend a different machine.
Do not invent information.
Do not use headings or bullet points.
""".strip()

        try:
            response = (
                await self.gemini_client.aio.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                )
            )

            if response.text and response.text.strip():
                return response.text.strip()

            return fallback

        except Exception as error:
            print(
                f"\nGemini no-selection explanation failed: "
                f"{error}"
            )
            return fallback