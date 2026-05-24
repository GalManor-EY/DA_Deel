from logic.join_diff import run as run_join_diff
from logic.in_payout_not_tms import run as run_payout_not_tms
from logic.in_tms_not_payout import run as run_tms_not_payout

def main():
    print("Running join_diff...")
    run_join_diff()

    print("Running in_payout_not_tms...")
    run_payout_not_tms()

    print("Running in_tms_not_in_payout...")
    run_tms_not_payout()

    print("All reconciliation steps completed ✅")

if __name__ == "__main__":
    main()