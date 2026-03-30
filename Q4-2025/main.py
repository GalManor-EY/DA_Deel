
from logic.join_diff_provider import run as run_join_diff_provider
from logic.payout_not_tms_cutoff import run as run_payout_not_tms_cutoff
from logic.tms_not_payout_cutoff import run as run_tms_not_payout_cutoff

def main():
    run_join_diff_provider()
    run_payout_not_tms_cutoff()
    run_tms_not_payout_cutoff()

if __name__ == "__main__":
    main()
