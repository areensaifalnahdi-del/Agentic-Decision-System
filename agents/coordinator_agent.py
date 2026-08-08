from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler
from services.logger import log_message

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

        # The 10 Machine Agents that the Coordinator will contact
        self.machine_agent_ids = [
            AgentId("machine_agent", "M01"),
            AgentId("machine_agent", "M02"),
            AgentId("machine_agent", "M03"),
            AgentId("machine_agent", "M04"),
            AgentId("machine_agent", "M05"),
            AgentId("machine_agent", "M06"),
            AgentId("machine_agent", "M07"),
            AgentId("machine_agent", "M08"),
            AgentId("machine_agent", "M09"),
            AgentId("machine_agent", "M10"),
        ]

        self.quality_agent_id = AgentId(
            "quality_agent",
            "default",
        )

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

        # -------------------------------------------------
        # STEP 1: Request the status of every machine
        # -------------------------------------------------

        machine_responses: list[MachineStatusResponse] = []

        for machine_agent_id in self.machine_agent_ids:
            machine_request = MachineStatusRequest(
                request_reason="order_evaluation",
                order_id=message.order_id,
            )

            log_message(
                "Coordinator",
                str(machine_agent_id),
                f"Machine status request for {message.order_id}",
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
                    f"{machine_agent_id} returned an invalid response."
                )

            machine_responses.append(machine_response)

            print(
                f"Coordinator received the status of "
                f"{machine_response.machine_id}"
            )

        # Convert machine responses into dictionaries
        machine_data = [
            machine_response.model_dump()
            for machine_response in machine_responses
        ]

        # -------------------------------------------------
        # STEP 2: Request quality assessments
        # -------------------------------------------------

        quality_request = QualityAssessmentRequest(
            order_id=message.order_id,
            quality_requirement=message.quality_requirement,
            machine_data=machine_data,
        )

        log_message(
            "Coordinator",
            "QualityAgent",
            f"Quality assessment request for {message.order_id}",
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

        # -------------------------------------------------
        # STEP 3: Request maintenance assessments
        # -------------------------------------------------

        maintenance_request = MaintenanceAssessmentRequest(
            machine_data=machine_data,
        )

        log_message(
            "Coordinator",
            "MaintenanceAgent",
            f"Maintenance assessment request for {message.order_id}",
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

        # -------------------------------------------------
        # Organize assessments by machine ID
        # -------------------------------------------------

        quality_by_machine = {
            assessment["machine_id"]: assessment
            for assessment in quality_response.assessments
        }

        maintenance_by_machine = {
            assessment["machine_id"]: assessment
            for assessment in maintenance_response.assessments
        }

        suitable_machines: list[tuple] = []
        machines_filtered_out: list[dict] = []

        # -------------------------------------------------
        # STEP 4: Apply deterministic decision rules
        # -------------------------------------------------

        for machine in machine_responses:

            rejection_reasons: list[str] = []

            quality_result = quality_by_machine.get(
                machine.machine_id
            )

            maintenance_result = maintenance_by_machine.get(
                machine.machine_id
            )

            # Check availability
            if machine.status != "available":
                rejection_reasons.append(
                    "machine is not available"
                )

            # Check required capability
            if machine.capability != message.required_capability:
                rejection_reasons.append(
                    "wrong capability"
                )

            # Check deadline
            if (
                machine.estimated_processing_time_mins
                > message.deadline_minutes
            ):
                rejection_reasons.append(
                    "cannot meet the deadline"
                )

            # Check quality result
            if quality_result is None:
                rejection_reasons.append(
                    "quality assessment is missing"
                )
            elif not quality_result.get(
                "is_suitable",
                False,
            ):
                rejection_reasons.append(
                    "failed the quality assessment"
                )

            # Check maintenance result
            if maintenance_result is None:
                rejection_reasons.append(
                    "maintenance assessment is missing"
                )
            elif (
                maintenance_result.get(
                    "availability_status"
                )
                != "available"
            ):
                rejection_reasons.append(
                    "failed the maintenance assessment"
                )

            # Store rejected or suitable machine
            if rejection_reasons:

                machines_filtered_out.append(
                    {
                        "machine_id": machine.machine_id,
                        "reason": ", ".join(
                            rejection_reasons
                        ),
                    }
                )

            else:

                suitable_machines.append(
                    (
                        machine,
                        quality_result,
                        maintenance_result,
                    )
                )

        # -------------------------------------------------
        # STEP 5: Select the best suitable machine
        # -------------------------------------------------

        if suitable_machines:

            selected = min(
                suitable_machines,
                key=lambda result: (
                    result[0].queue_length,
                    result[1].get(
                        "quality_risk_score",
                        1.0,
                    ),
                    result[0].estimated_processing_time_mins,
                ),
            )

            selected_machine = selected[0]
            selected_quality = selected[1]
            selected_maintenance = selected[2]

            selected_machine_id = selected_machine.machine_id

            justification = (
                f"{selected_machine.machine_id} was selected because "
                f"it has the required "
                f"{message.required_capability} capability, "
                f"is available, can meet the deadline, "
                f"and passed the quality and maintenance checks."
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

        else:

            selected_machine = None
            selected_quality = None
            selected_maintenance = None

            selected_machine_id = "none"

            justification = (
                "No machine satisfied all order, quality, "
                "and maintenance requirements."
            )

            required_actions = {
                "quality": "none",
                "maintenance": "none",
            }

        # -------------------------------------------------
        # STEP 6: Build structured evidence package
        # -------------------------------------------------

        evidence = {
            "order": {
                "order_id": message.order_id,
                "required_capability": message.required_capability,
                "quality_requirement": message.quality_requirement,
                "deadline_minutes": message.deadline_minutes,
            },
            "selected_machine": (
                {
                    "machine_id": selected_machine.machine_id,
                    "status": selected_machine.status,
                    "capability": selected_machine.capability,
                    "queue_length": selected_machine.queue_length,
                    "processing_time_minutes": (
                        selected_machine.estimated_processing_time_mins
                    ),
                    "maintenance_condition": (
                        selected_machine.maintenance_condition
                    ),
                    "active_warnings": selected_machine.active_warnings,
                    "quality_risk_score": selected_quality.get(
                        "quality_risk_score"
                    ),
                    "quality_suitable": selected_quality.get(
                        "is_suitable"
                    ),
                    "maintenance_status": selected_maintenance.get(
                        "availability_status"
                    ),
                    "maintenance_action": selected_maintenance.get(
                        "maintenance_action_required"
                    ),
                }
                if selected_machine is not None
                else None
            ),
            "rejected_machines": machines_filtered_out,
        }

        # -------------------------------------------------
        # STEP 7: Create final recommendation
        # -------------------------------------------------

        final_recommendation = FinalRecommendation(
            order_id=message.order_id,
            selected_machine=selected_machine_id,
            justification=justification,
            required_actions=required_actions,
            machines_filtered_out=machines_filtered_out,
            evidence=evidence,
        )

        print("Coordinator created the final recommendation")

        return final_recommendation
