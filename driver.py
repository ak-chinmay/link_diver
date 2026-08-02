"""Backward-compatible executable for Link Diver.

The application implementation lives in the :mod:`link_diver` package. Keeping
this small wrapper means existing cron jobs and shell scripts can continue to
run ``python3 driver.py``.
"""

from link_diver.cli import main


if __name__ == "__main__":
    main()
