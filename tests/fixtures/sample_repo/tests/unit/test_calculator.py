"""Unit tests for Calculator — pure logic, no external dependencies."""
import unittest
from unittest.mock import MagicMock, patch


class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Division by zero")
        return a / b


class TestCalculatorAdd(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_add_positive_numbers(self):
        self.assertEqual(self.calc.add(2, 3), 5)

    def test_add_negative_numbers(self):
        self.assertEqual(self.calc.add(-1, -1), -2)

    def test_add_zero(self):
        self.assertEqual(self.calc.add(0, 5), 5)


class TestCalculatorDivide(unittest.TestCase):
    def setUp(self):
        self.calc = Calculator()

    def test_divide_valid(self):
        self.assertAlmostEqual(self.calc.divide(10, 2), 5.0)

    def test_divide_by_zero_raises(self):
        with self.assertRaises(ValueError):
            self.calc.divide(10, 0)

    def test_divide_uses_mock_logger(self):
        mock_logger = MagicMock()
        with patch("logging.getLogger", return_value=mock_logger):
            result = self.calc.divide(6, 3)
        self.assertEqual(result, 2.0)


if __name__ == "__main__":
    unittest.main()
