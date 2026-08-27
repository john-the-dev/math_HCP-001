#!/usr/bin/env python3
import pathlib
import re
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parent


def run(binary, *args):
    return subprocess.run(
        [str(binary), *args], text=True, capture_output=True, check=False
    )


def main():
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = pathlib.Path(tmp_name)
        binary = tmp / "z43_tabu"
        subprocess.run(
            [
                "c++", "-O2", "-DNDEBUG", "-std=c++20", "-Wall", "-Wextra",
                "-Wpedantic", str(ROOT / "z43_tabu.cpp"), "-o", str(binary),
            ],
            check=True,
        )

        default_graph = tmp / "default.txt"
        explicit_graph = tmp / "explicit.txt"
        default = run(binary, "--seconds", "0", "--output", str(default_graph))
        explicit = run(
            binary, "--seconds", "0", "--kick-min", "8", "--kick-max", "24",
            "--output", str(explicit_graph),
        )
        assert default.returncode == explicit.returncode == 2
        scrub_elapsed = lambda value: re.sub(
            r"elapsed_seconds=[^ ]+", "elapsed_seconds=<clock>", value
        )
        assert scrub_elapsed(default.stdout) == scrub_elapsed(explicit.stdout)
        assert default_graph.read_bytes() == explicit_graph.read_bytes()

        fixed = run(
            binary, "--seconds", "0.05", "--restart-after", "1",
            "--kick-min", "64", "--kick-max", "64",
            "--output", str(tmp / "fixed.txt"),
        )
        assert fixed.returncode == 2
        restarts = re.search(r"restarts=(\d+)", fixed.stdout)
        assert restarts is not None and int(restarts.group(1)) > 0

        for bounds in (("-1", "8"), ("25", "24"), ("0", "904")):
            invalid = run(binary, "--kick-min", bounds[0], "--kick-max", bounds[1])
            assert invalid.returncode != 0
            assert "kick range must satisfy" in invalid.stderr

    print("CLI_TESTS=PASS")


if __name__ == "__main__":
    main()
