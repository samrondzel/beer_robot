import json
import serial

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ESP32BridgeNode(Node):
    def __init__(self):
        super().__init__("esp32_bridge_node")

        self.esp = serial.Serial(
            "/dev/ttyUSB0",
            115200,
            timeout=1
        )

        self.subscriber = self.create_subscription(
            String,
            "/target_state",
            self.on_target_state,
            10
        )

        self.get_logger().info("ESP32 bridge node started")


    def on_target_state(self, msg: String):
        try:
            state = json.loads(msg.data)

            left = float(state.get("left_speed", 0.0))
            right = float(state.get("right_speed", 0.0))
            command_text = state.get("command_text", "")
            locked = bool(state.get("locked", False))

            if not locked:
                command = "STOP\n"
            else:
                command = f"MOVE {left:.2f} {right:.2f}\n"

            self.esp.write(command.encode())
            response = self.esp.readline().decode().strip()

            if response:
                self.get_logger().info(
                    f"ESP32 says: {response}"
                )

            self.get_logger().info(
                f"target_cmd={command_text} | sent_to_esp32={command.strip()}"
            )

        except Exception as e:
            self.get_logger().error(f"Failed to process target_state: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ESP32BridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()