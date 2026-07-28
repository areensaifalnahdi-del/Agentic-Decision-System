from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler

from messages.order_message import OrderMessage
from messages.machine_status_request import MachineStatusRequest
from messages.machine_status_response import MachineStatusResponse
from messages.quality_assessment_request import QualityAssessmentRequest
from messages.quality_assessment_response import QualityAssessmentResponse
from messages.maintenance_assessment_request import (
    MaintenanceAssessmentRequest,
)
from messages.maintenance_assessment_response import (
    MaintenanceAssessmentResponse,
)
from messages.final_recommendation import FinalRecommendation


class CoordinatorAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__(
            description="Coordinates the manufacturing decision workflow."
        )

        # These IDs must match the IDs used when registering the agents.
        self.machine_agent_id = AgentId("machine_agent", "M01")
        self.quality_agent_id = AgentId("quality_agent", "default")
        self.maintenance_agent_id = AgentId(
            "maintenance_agent",
            "default",
        )

    @message_handler
    async def handle_order(
        self,
        message: OrderMessage,
        ctx: MessageContext,
    ) -> FinalRecommendation:
        print(f"Coordinator received order {message.order_id}")

        # STEP 1: Request machine information.
        machine_request = MachineStatusRequest(
            request_reason="order_evaluation",
            order_id=message.order_id,
        )

        machine_response = await self.send_message(
            machine_request,
            recipient=self.machine_agent_id,
        )

        if not isinstance(machine_response, MachineStatusResponse):
            raise TypeError(
                "The Machine Agent returned an invalid response."
            )

        print(
            f"Coordinator received the status of "
            f"{machine_response.machine_id}"
        )

        machine_data = [machine_response.model_dump()]

        # STEP 2: Request a quality assessment.
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

        print("Coordinator received the quality assessment")

        # STEP 3: Request a maintenance assessment.
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

        print("Coordinator received the maintenance assessment")

        quality_result = quality_response.assessments[0]
        maintenance_result = maintenance_response.assessments[0]

        # STEP 4: Apply fixed decision rules.
        rejection_reasons: list[str] = []

        if machine_response.status != "available":
            rejection_reasons.append(
                "the machine is not available"
            )

        if (
            machine_response.capability
            != message.required_capability
        ):
            rejection_reasons.append(
                "the machine has the wrong capability"
            )

        if (
            machine_response.estimated_processing_time_mins
            > message.deadline_minutes
        ):
            rejection_reasons.append(
                "the machine cannot meet the deadline"
            )

        if not quality_result.get("is_suitable", False):
            rejection_reasons.append(
                "the machine did not pass the quality assessment"
            )

        if (
            maintenance_result.get("availability_status")
            != "available"
        ):
            rejection_reasons.append(
                "the machine did not pass the maintenance assessment"
            )

        # STEP 5: Create the final recommendation.
        if rejection_reasons:
            selected_machine = "none"

            justification = (
                f"{machine_response.machine_id} was rejected because "
                + ", ".join(rejection_reasons)
                + "."
            )

            machines_filtered_out = [
                {
                    "machine_id": machine_response.machine_id,
                    "reason": ", ".join(rejection_reasons),
                }
            ]

        else:
            selected_machine = machine_response.machine_id

            justification = (
                f"{machine_response.machine_id} was selected because "
                f"it has the required "
                f"{message.required_capability} capability, "
                f"is available, can meet the deadline, "
                f"and passed the quality and maintenance checks."
            )

            machines_filtered_out = []

        final_recommendation = FinalRecommendation(
            order_id=message.order_id,
            selected_machine=selected_machine,
            justification=justification,
            required_actions={
                "quality": quality_result.get(
                    "recommended_action",
                    "none",
                ),
                "maintenance": maintenance_result.get(
                    "maintenance_action_required",
                    "none",
                ),
            },
            machines_filtered_out=machines_filtered_out,
        )

        print("Coordinator created the final recommendation")

        return final_recommendation