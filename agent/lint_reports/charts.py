"""Tiny SVG trend chart renderer with no third-party dependencies."""

from typing import List, Tuple


class SvgTrendPlotter:
    """Renders line charts for lint trends."""

    _palette = [
        "#d62728",
        "#ff7f0e",
        "#1f77b4",
        "#2ca02c",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]

    def render(
        self,
        title: str,
        x_labels: List[str],
        series: List[Tuple[str, List[int]]],
        output_path: str,
        width: int = 1100,
        height: int = 520,
    ) -> None:
        if not series:
            series = [("No data", [0 for _ in x_labels])]

        left = 70
        right = 260
        top = 50
        bottom = 70

        plot_width = max(200, width - left - right)
        plot_height = max(150, height - top - bottom)
        x_count = max(1, len(x_labels))
        x_step = float(plot_width) / max(1, x_count - 1)

        max_value = 0
        for _name, values in series:
            if values:
                max_value = max(max_value, max(values))
        y_max = max(1, max_value)

        svg_lines: List[str] = []
        svg_lines.append(
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">'
            % (width, height)
        )
        svg_lines.append(
            '<rect x="0" y="0" width="%d" height="%d" fill="#ffffff"/>'
            % (width, height)
        )
        svg_lines.append(
            '<text x="%d" y="30" font-size="20" font-family="Arial" fill="#111">%s</text>'
            % (left, self._escape(title))
        )

        # Grid lines and Y ticks.
        for tick in range(0, 6):
            y_value = int(round(float(y_max) * tick / 5.0))
            y = top + plot_height - int(round(float(plot_height) * tick / 5.0))
            svg_lines.append(
                '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#e6e6e6" stroke-width="1"/>'
                % (left, y, left + plot_width, y)
            )
            svg_lines.append(
                '<text x="%d" y="%d" font-size="11" font-family="Arial" fill="#333" text-anchor="end">%d</text>'
                % (left - 8, y + 4, y_value)
            )

        # Axes.
        svg_lines.append(
            '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="1.2"/>'
            % (left, top + plot_height, left + plot_width, top + plot_height)
        )
        svg_lines.append(
            '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#333" stroke-width="1.2"/>'
            % (left, top, left, top + plot_height)
        )

        # X labels.
        label_step = max(1, len(x_labels) // 12)
        for idx, label in enumerate(x_labels):
            if idx % label_step != 0 and idx != len(x_labels) - 1:
                continue
            x = left + int(round(idx * x_step))
            svg_lines.append(
                '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#666" stroke-width="1"/>'
                % (x, top + plot_height, x, top + plot_height + 4)
            )
            svg_lines.append(
                '<text x="%d" y="%d" font-size="10" font-family="Arial" fill="#333" text-anchor="middle">%s</text>'
                % (x, top + plot_height + 18, self._escape(label))
            )

        # Series lines and points.
        for index, (name, values) in enumerate(series):
            color = self._palette[index % len(self._palette)]
            points: List[str] = []
            for idx, value in enumerate(values):
                x = left + int(round(idx * x_step))
                y = (
                    top
                    + plot_height
                    - int(round((float(value) / float(y_max)) * plot_height))
                )
                points.append("%d,%d" % (x, y))
            svg_lines.append(
                '<polyline fill="none" stroke="%s" stroke-width="2.2" points="%s"/>'
                % (color, " ".join(points))
            )
            for point in points:
                x_val, y_val = point.split(",")
                svg_lines.append(
                    '<circle cx="%s" cy="%s" r="2.5" fill="%s"/>'
                    % (x_val, y_val, color)
                )

            legend_x = left + plot_width + 20
            legend_y = top + 24 + index * 20
            svg_lines.append(
                '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2.5"/>'
                % (legend_x, legend_y, legend_x + 22, legend_y, color)
            )
            svg_lines.append(
                '<text x="%d" y="%d" font-size="11" font-family="Arial" fill="#111">%s</text>'
                % (legend_x + 28, legend_y + 4, self._escape(name))
            )

        svg_lines.append(
            '<text x="%d" y="%d" font-size="11" font-family="Arial" fill="#444">Run sequence</text>'
            % (left + plot_width // 2, height - 20)
        )
        svg_lines.append("</svg>")

        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(svg_lines) + "\n")

    @staticmethod
    def _escape(value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
