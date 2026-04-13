# staging/load_all.py

from staging.load_payout import load_payout
from staging.load_TMS import load_tms
from staging.load_full_payout import load_full_payout

def main():
    load_payout()
    load_tms()
    load_full_payout()
if __name__ == "__main__":
    main()
