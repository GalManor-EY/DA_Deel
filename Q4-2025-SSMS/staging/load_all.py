# staging/load_all.py

from staging.load_payout import load_payout
from staging.load_TMS import load_tms

def main():
    load_payout()
    load_tms()

if __name__ == "__main__":
    main()
