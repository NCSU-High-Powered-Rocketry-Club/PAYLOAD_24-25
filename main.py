# For Command line arguments
import argparse

# Payload module
import spaceducks


# Program description
msg = "Main HPRC Payload Program for 2024-2025."

# Initialize parser
parser = argparse.ArgumentParser(description=msg)

# TODO: Add any arguments we might need
# parser.add_argument("-f", "--Frequency", help="APRS Frequency in MHz")

args = parser.parse_args()


def main(args):

    payload = spaceducks.PayloadSystem()

    try:
        while payload.running:
            payload.update()

    except KeyboardInterrupt:
        # Early shutdown if interrupted
        payload.shutdown()

    print(str(payload.CALLSIGN) + "-> Max Altitude: " + str(payload.stats.max_altitude))
    print("Program complete. Waiting for recovery.")


if __name__ == "__main__":
    main(args)
