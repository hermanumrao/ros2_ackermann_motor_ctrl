import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import time


class ArduinoBridge(Node):
    def __init__(self):
        super().__init__("arduino_bridge")

        self.port_name = "/dev/ttyUSB0"
        self.baudrate = 115200

        self.serial_port = None
        self.connect_serial()

        # ROS subscriber
        self.subscription = self.create_subscription(
            String,
            "motor_command",
            self.command_callback,
            10
        )

        # Heartbeat (slower, safer)
        self.heartbeat_timer = self.create_timer(1.0, self.send_heartbeat)

    # ================= SERIAL =================
    def connect_serial(self):
        try:
            self.get_logger().info("Connecting to serial...")

            self.serial_port = serial.Serial(
                self.port_name,
                self.baudrate,
                timeout=0.1,        # non-blocking read
                dsrdtr=False,
                rtscts=False
            )

            # Prevent auto reset issue
            self.serial_port.setDTR(False)

            time.sleep(2)  # 🔴 CRITICAL: allow Arduino to stabilize

            self.get_logger().info("Serial connected and ready")

        except Exception as e:
            self.get_logger().error(f"Serial connection failed: {e}")
            self.serial_port = None

    def write_serial(self, data):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write((data + "\n").encode("utf-8"))
            except Exception as e:
                self.get_logger().error(f"Serial write failed: {e}")
                self.serial_port.close()
                self.serial_port = None
        else:
            self.get_logger().warn("Serial not connected. Retrying...")
            self.connect_serial()

    # ================= ROS CALLBACK =================
    def command_callback(self, msg):
        command = msg.data.strip().upper()

        if not command:
            return

        self.get_logger().info(f"TX → {command}")
        self.write_serial(command)

    # ================= HEARTBEAT =================
    def send_heartbeat(self):
        self.write_serial("HEARTBEAT")


def main(args=None):
    rclpy.init(args=args)

    node = ArduinoBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    if node.serial_port and node.serial_port.is_open:
        node.serial_port.close()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
