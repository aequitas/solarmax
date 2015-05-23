Script to read Solarmax Inverter and output metrics in graphite compatible format.

Installation:

    pip install -e git+https://github.com/aequitas/solarmax.git#egg=solarmax

Usage (using bash):

    solarmax >/dev/tcp/graphite-host/2003

Based on: https://github.com/pdmct/solarmax-agent
