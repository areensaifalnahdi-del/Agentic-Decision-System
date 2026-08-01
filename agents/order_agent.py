from autogen_core import MessageContext, RoutedAgent, message_handler

from messages.order_message import OrderMessage


class OrderAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__(
            description="Creates and validates urgent production orders."
        )

    @message_handler
    async def handle_order_creation(
        self,
        message: OrderMessage,
        ctx: MessageContext,
    ) -> OrderMessage:
        """
        Receive and validate an order through the AutoGen runtime.
        """

        print(f"Order Agent received order {message.order_id}")

        validated_order = OrderMessage(
            order_id=message.order_id,
            priority=message.priority,
            required_capability=message.required_capability,
            deadline_minutes=message.deadline_minutes,
            quality_requirement=message.quality_requirement,
        )

        print(
            f"Order Agent validated order "
            f"{validated_order.order_id}"
        )

        return validated_order