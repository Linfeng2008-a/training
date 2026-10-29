import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from rm_msgs.msg import WheelLegCmd
import math

class WheelLegController(Node):
    def __init__(self):
        super().__init__('wheel_leg_controller')
        
        self.sub = self.create_subscription(JointState, '/joint_states', self.state_callback, 10)
        self.pub = self.create_publisher(WheelLegCmd, '/actuator_cmd', 10)
        
        self.timer = self.create_timer(0.01, self.control_loop)
        self.current_state = None

    def state_callback(self, msg):
        self.current_state = msg

    def control_loop(self):
        if self.current_state is None:
            return
        
        cmd = WheelLegCmd()
        
        # 1. 腿部关节给一个较大的力，尝试支撑住身体（你可以调大这个 2.0）
        cmd.right_phi1 = 2.0
        cmd.right_phi4 = 2.0
        cmd.left_phi1 = 2.0
        cmd.left_phi4 = 2.0
        
        # 2. 尝试获取底盘的倾斜角（通常存在于前几个位置数据中）
        # 这里的索引 [0] 或者 [1] 可能是角度，如果不准，你可以改成 [1] 或 [2]
        # 因为不知道确切模型，我们假设底盘角度在 position[2] 左右
        pitch = self.current_state.position[2] if len(self.current_state.position) > 2 else 0.0
        
        # 3. PD 控制核心逻辑：根据倾斜角度和轮子速度，计算该给多大的力
        # 如果角度大于0（往前倒），轮子就要往前加速（把重心拉回来）
        kp = 5.0  # 角度补偿系数
        kd = 1.0  # 速度阻尼系数
        
        right_wheel_vel = self.current_state.velocity[4] if len(self.current_state.velocity) > 4 else 0.0
        left_wheel_vel = self.current_state.velocity[5] if len(self.current_state.velocity) > 5 else 0.0
        
        # 计算控制量
        control_signal = (pitch * kp) - ((right_wheel_vel + left_wheel_vel) / 2.0 * kd)
        
        # 限制最大力矩，防止它飞出屏幕（最大不能超过 2.0）
        control_signal = max(min(control_signal, 2.0), -2.0)
        
        cmd.right_wheel = control_signal
        cmd.left_wheel = control_signal
        
        # 4. 打印实时状态，方便观察
        self.get_logger().info(f"Pitch: {pitch:.2f}, 轮子力矩: {control_signal:.2f}")
        
        self.pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = WheelLegController()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()