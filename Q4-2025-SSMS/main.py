from logic.join_diff import run as run_join_diff
from logic.in_payout_not_tms import run as run_payout_not_tms
from logic.in_tms_not_payout import run as run_tms_not_payout

def main():
    run_join_diff()
    run_payout_not_tms()
    run_tms_not_payout()

if __name__ == "__main__":
    main()
