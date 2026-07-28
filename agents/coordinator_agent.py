from messages.order_message import OrderMessage
from messages.machine_status_request import MachineStatusRequest
from messages.quality_assessment_request import QualityAssessmentRequest
from messages.maintenance_assessment_request import (
    MaintenanceAssessmentRequest,
)
from messages.final_recommendation import FinalRecommendation


class CoordinatorAgent:
    def __init__(
        self,
        machine_agents,
        quality_agent,
        maintenance_agents,
    ):
        self.machine_agents = machine_agents
        self.quality_agent = quality_agent
        self.maintenance_agents = maintenance_agents

    def handle_order(
        self,
        order: OrderMessage,
    ) -> FinalRecommendation:
        print(
            f"\nCoordinator Agent received order {order.order_id}."
        )

        # -----------------------------------------
        # 1. Request status from every machine
        # -----------------------------------------

        status_request = MachineStatusRequest(
            request_reason="order_evaluation",
            order_id=order.order_id,
        )

        machine_responses = []

        for machine_agent in self.machine_agents:
            response = machine_agent.handle_status_request(
                status_request
            )
            machine_responses.append(response)

        # -----------------------------------------
        # 2. Request quality assessments
        # -----------------------------------------

        quality_request = QualityAssessmentRequest(
            order_id=order.order_id,
            quality_requirement=order.quality_requirement,
            machine_data=[
                {
                    "machine_id": machine.machine_id,
                    "active_warnings": machine.active_warnings,
                }
                for machine in machine_responses
            ],
        )

        quality_response = (
            self.quality_agent.handle_quality_request(
                quality_request
            )
        )

        # -----------------------------------------
        # 3. Request maintenance assessments
        # -----------------------------------------

        maintenance_request = MaintenanceAssessmentRequest(
            machine_data=[
                {
                    "machine_id": machine.machine_id,
                    "maintenance_condition": (
                        machine.maintenance_condition
                    ),
                    "active_warnings": machine.active_warnings,
                }
                for machine in machine_responses
            ]
        )

        maintenance_assessments = []

        for maintenance_agent in self.maintenance_agents:
            response = (
                maintenance_agent.handle_maintenance_request(
                    maintenance_request
                )
            )

            maintenance_assessments.extend(
                response.assessments
            )

        # -----------------------------------------
        # 4. Create lookup tables
        # -----------------------------------------

        quality_by_machine = {
            assessment["machine_id"]: assessment
            for assessment in quality_response.assessments
        }

        maintenance_by_machine = {
            assessment["machine_id"]: assessment
            for assessment in maintenance_assessments
        }

        # -----------------------------------------
        # 5. Apply filtering rules
        # -----------------------------------------

        candidates = []
        filtered_out = []

        for machine in machine_responses:
            machine_id = machine.machine_id

            quality = quality_by_machine[machine_id]
            maintenance = maintenance_by_machine[machine_id]

            reason = None

            if maintenance["availability_status"] == "blocked":
                reason = "blocked by maintenance"

            elif (
                machine.capability.lower()
                != order.required_capability.lower()
            ):
                reason = "wrong capability"

            elif machine.status.lower() in {
                "maintenance",
                "offline",
            }:
                reason = f"machine status is {machine.status}"

            elif not quality["is_suitable"]:
                reason = "quality risk is too high"

            elif (
                machine.estimated_processing_time_mins
                > order.deadline_minutes
            ):
                reason = "cannot meet the deadline"

            if reason:
                filtered_out.append(
                    {
                        "machine_id": machine_id,
                        "reason": reason,
                    }
                )

            else:
                candidates.append(
                    {
                        "machine": machine,
                        "quality": quality,
                        "maintenance": maintenance,
                    }
                )

        # -----------------------------------------
        # 6. Handle no suitable machine
        # -----------------------------------------

        if not candidates:
            return FinalRecommendation(
                order_id=order.order_id,
                selected_machine="NONE",
                justification=(
                    "No machine satisfied all capability, "
                    "quality, maintenance, and deadline rules."
                ),
                required_actions={
                    "quality": "review required",
                    "maintenance": "review required",
                },
                machines_filtered_out=filtered_out,
            )

        # -----------------------------------------
        # 7. Rank suitable machines
        # -----------------------------------------

        candidates.sort(
            key=lambda candidate: (
                candidate["machine"].queue_length,
                candidate["quality"]["quality_risk_score"],
                candidate[
                    "machine"
                ].estimated_processing_time_mins,
            )
        )

        best = candidates[0]

        selected_machine = best["machine"]
        selected_quality = best["quality"]
        selected_maintenance = best["maintenance"]

        # -----------------------------------------
        # 8. Create final recommendation
        # -----------------------------------------

        return FinalRecommendation(
            order_id=order.order_id,
            selected_machine=selected_machine.machine_id,
            justification=(
                f"{selected_machine.machine_id} has the "
                f"required {order.required_capability} capability, "
                f"a queue length of "
                f"{selected_machine.queue_length}, "
                f"a quality risk score of "
                f"{selected_quality['quality_risk_score']}, "
                f"and can complete the job within "
                f"{selected_machine.estimated_processing_time_mins} "
                "minutes."
            ),
            required_actions={
                "quality": selected_quality[
                    "recommended_action"
                ],
                "maintenance": selected_maintenance[
                    "maintenance_action_required"
                ],
            },
            machines_filtered_out=filtered_out,
        )