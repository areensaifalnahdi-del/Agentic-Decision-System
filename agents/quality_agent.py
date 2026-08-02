from autogen_core import MessageContext, RoutedAgent, message_handler

from messages.quality_assessment_request import QualityAssessmentRequest
from messages.quality_assessment_response import QualityAssessmentResponse


class QualityAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__(
            description="Evaluates whether machines satisfy the quality requirement."
        )

        # FMEA risk table
        self.fmea_table = {
            "critical_fault": {
                "risk": 0.8,
                "action": "reject machine and perform maintenance check",
                "suitable": False,
            },
            "overheating": {
                "risk": 0.8,
                "action": "reject machine and perform maintenance check",
                "suitable": False,
            },
            "minor_vibration": {
                "risk": 0.3,
                "action": "continue production with observation",
                "suitable": True,
            },
            "tool_wear": {
                "risk": 0.5,
                "action": "inspect machine before production",
                "suitable": True,
            },
        }

    @message_handler
    async def handle_quality_request(
        self,
        message: QualityAssessmentRequest,
        ctx: MessageContext,
    ) -> QualityAssessmentResponse:

        print(
            f"Quality Agent received an AutoGen request "
            f"for order {message.order_id}"
        )

        assessments: list[dict] = []

        for machine in message.machine_data:
            machine_id = machine.get("machine_id", "unknown")
            warnings = machine.get("active_warnings", [])

            risk_score = 0.1
            recommended_action = "continue production"
            is_suitable = True

            # Apply FMEA rules
            for warning in warnings:
                if warning in self.fmea_table:
                    failure = self.fmea_table[warning]

                    risk_score = failure["risk"]
                    recommended_action = failure["action"]
                    is_suitable = failure["suitable"]

                    break

            assessments.append(
                {
                    "machine_id": machine_id,
                    "quality_risk_score": risk_score,
                    "recommended_action": recommended_action,
                    "is_suitable": is_suitable,
                }
            )

        return QualityAssessmentResponse(
            assessments=assessments
        )
