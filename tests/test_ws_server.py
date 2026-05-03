import asyncio
import contextlib
import io
import unittest

from network import ws_server


class FakeChannel:
    def __init__(self):
        self.history = []
        self._duty_cycle = None
        self.duty_cycle = None

    @property
    def duty_cycle(self):
        return self._duty_cycle

    @duty_cycle.setter
    def duty_cycle(self, value):
        self.history.append(value)
        self._duty_cycle = value


class IdleAfterOneMessageWebSocket:
    remote_address = ("test-client", 12345)

    def __init__(self, message, outputs):
        self.message = message
        self.outputs = outputs
        self.messages_sent = 0
        self.outputs_during_idle = None

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages_sent == 0:
            self.messages_sent += 1
            return self.message

        await asyncio.sleep(
            ws_server.FAILSAFE_TIMEOUT_S + (ws_server.WATCHDOG_PERIOD_S * 3)
        )
        self.outputs_during_idle = (
            self.outputs.steering_channel.duty_cycle,
            self.outputs.throttle_channel.duty_cycle,
        )
        raise StopAsyncIteration


class WsServerTests(unittest.TestCase):
    def setUp(self):
        self.steering = FakeChannel()
        self.throttle = FakeChannel()
        self.outputs = ws_server.RobotOutputs(self.steering, self.throttle)

    def test_ms_to_duty(self):
        self.assertEqual(ws_server.ms_to_duty(1.50), int((1.50 / 20.0) * 65535))

    def test_steering_mapping_clamps_and_interpolates(self):
        self.assertEqual(ws_server.steering_ms_from_unit(-2.0), ws_server.LEFT_MS)
        self.assertEqual(ws_server.steering_ms_from_unit(-1.0), ws_server.LEFT_MS)
        self.assertEqual(ws_server.steering_ms_from_unit(0.0), ws_server.CENTER_MS)
        self.assertEqual(ws_server.steering_ms_from_unit(1.0), ws_server.RIGHT_MS)
        self.assertEqual(ws_server.steering_ms_from_unit(2.0), ws_server.RIGHT_MS)
        self.assertAlmostEqual(ws_server.steering_ms_from_unit(0.5), 1.65)
        self.assertAlmostEqual(ws_server.steering_ms_from_unit(-0.5), 1.35)

    def test_throttle_mapping_clamps_and_interpolates(self):
        self.assertEqual(ws_server.throttle_ms_from_unit(-2.0), ws_server.THROTTLE_REVERSE_MS)
        self.assertEqual(ws_server.throttle_ms_from_unit(-1.0), ws_server.THROTTLE_REVERSE_MS)
        self.assertEqual(ws_server.throttle_ms_from_unit(0.0), ws_server.THROTTLE_NEUTRAL_MS)
        self.assertEqual(ws_server.throttle_ms_from_unit(1.0), ws_server.THROTTLE_FORWARD_MS)
        self.assertEqual(ws_server.throttle_ms_from_unit(2.0), ws_server.THROTTLE_FORWARD_MS)
        self.assertAlmostEqual(ws_server.throttle_ms_from_unit(-0.5), 1.25)
        self.assertAlmostEqual(ws_server.throttle_ms_from_unit(0.5), 1.75)

    def test_outputs_write_pwm_duty_cycles(self):
        self.outputs.set_steering_unit(1.0)
        self.outputs.set_throttle_unit(1.0)

        self.assertEqual(self.steering.duty_cycle, ws_server.ms_to_duty(ws_server.RIGHT_MS))
        self.assertEqual(self.throttle.duty_cycle, ws_server.ms_to_duty(ws_server.THROTTLE_FORWARD_MS))

    def test_outputs_set_safe_centers_and_stops(self):
        self.outputs.set_steering_unit(1.0)
        self.outputs.set_throttle_unit(1.0)

        self.outputs.set_safe()

        self.assertEqual(self.steering.duty_cycle, ws_server.ms_to_duty(ws_server.CENTER_MS))
        self.assertEqual(self.throttle.duty_cycle, ws_server.ms_to_duty(ws_server.THROTTLE_NEUTRAL_MS))

    def test_apply_message_defaults_missing_values_to_safe(self):
        steering, throttle = ws_server.apply_message(self.outputs, "{}")

        self.assertEqual((steering, throttle), (0.0, 0.0))
        self.assertEqual(self.steering.duty_cycle, ws_server.ms_to_duty(ws_server.CENTER_MS))
        self.assertEqual(self.throttle.duty_cycle, ws_server.ms_to_duty(ws_server.THROTTLE_NEUTRAL_MS))

    def test_apply_message_sets_requested_outputs(self):
        steering, throttle = ws_server.apply_message(
            self.outputs, '{"steering": -0.5, "throttle": 0.5}'
        )

        self.assertEqual((steering, throttle), (-0.5, 0.5))
        self.assertEqual(self.steering.duty_cycle, ws_server.ms_to_duty(1.35))
        self.assertEqual(self.throttle.duty_cycle, ws_server.ms_to_duty(1.75))

    def test_apply_message_sets_reverse_throttle(self):
        steering, throttle = ws_server.apply_message(
            self.outputs, '{"steering": 0.25, "throttle": -0.5}'
        )

        self.assertEqual((steering, throttle), (0.25, -0.5))
        self.assertEqual(self.steering.duty_cycle, ws_server.ms_to_duty(1.575))
        self.assertEqual(self.throttle.duty_cycle, ws_server.ms_to_duty(1.25))

    def test_apply_message_rejects_bad_input_without_changing_outputs(self):
        self.outputs.set_safe()

        with self.assertRaises(ValueError):
            ws_server.apply_message(self.outputs, '{"steering": "left"}')

        self.assertEqual(self.steering.duty_cycle, ws_server.ms_to_duty(ws_server.CENTER_MS))
        self.assertEqual(self.throttle.duty_cycle, ws_server.ms_to_duty(ws_server.THROTTLE_NEUTRAL_MS))


class WsServerAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_handler_watchdog_sets_outputs_safe_when_client_goes_idle(self):
        old_failsafe_timeout = ws_server.FAILSAFE_TIMEOUT_S
        old_watchdog_period = ws_server.WATCHDOG_PERIOD_S
        ws_server.FAILSAFE_TIMEOUT_S = 0.02
        ws_server.WATCHDOG_PERIOD_S = 0.005

        steering = FakeChannel()
        throttle = FakeChannel()
        outputs = ws_server.RobotOutputs(steering, throttle)
        websocket = IdleAfterOneMessageWebSocket(
            '{"steering": 1.0, "throttle": 1.0}', outputs
        )

        try:
            with contextlib.redirect_stdout(io.StringIO()):
                await ws_server.handler(websocket, outputs)
        finally:
            ws_server.FAILSAFE_TIMEOUT_S = old_failsafe_timeout
            ws_server.WATCHDOG_PERIOD_S = old_watchdog_period

        self.assertEqual(
            websocket.outputs_during_idle,
            (
                ws_server.ms_to_duty(ws_server.CENTER_MS),
                ws_server.ms_to_duty(ws_server.THROTTLE_NEUTRAL_MS),
            ),
        )
        self.assertIn(ws_server.ms_to_duty(ws_server.RIGHT_MS), steering.history)
        self.assertIn(ws_server.ms_to_duty(ws_server.THROTTLE_FORWARD_MS), throttle.history)


if __name__ == "__main__":
    unittest.main()
