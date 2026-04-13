# staging/load_all.py

from staging.load_payout import load_payout
from staging.load_TMS import load_tms
from staging.load_full_payout import load_full_payout
from staging.load_full_TMS import load_full_tms
from staging.load_payment_contractor_withdrawal import load_payment_contractor_withdrawal


def main():
    load_payout()
    load_tms()
    load_full_payout()
    load_full_tms()
    load_payment_contractor_withdrawal()
if __name__ == "__main__":
    main()
