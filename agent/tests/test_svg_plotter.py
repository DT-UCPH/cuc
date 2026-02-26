import tempfile
import unittest
from pathlib import Path

from lint_reports.charts import SvgTrendPlotter


class SvgTrendPlotterTest(unittest.TestCase):
    def test_render_creates_svg_file(self):
        plotter = SvgTrendPlotter()
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "chart.svg"
            plotter.render(
                title="Test Chart",
                x_labels=["1", "2", "3"],
                series=[("ERROR", [10, 8, 6]), ("WARNING", [3, 4, 2])],
                output_path=str(out_path),
            )
            content = out_path.read_text(encoding="utf-8")
            self.assertIn("<svg", content)
            self.assertIn("Test Chart", content)
            self.assertIn("ERROR", content)


if __name__ == "__main__":
    unittest.main()
