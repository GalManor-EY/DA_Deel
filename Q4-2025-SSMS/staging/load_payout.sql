/* staging/load_payout.sql
   Creates: payout_q4_25
*/


DROP TABLE IF EXISTS dbo.stg_payout_q4_2025;
SELECT *
INTO dbo.stg_payout_q4_2025
FROM OPENROWSET(
    BULK 'C:\Users\Gal.Manor\EY\IL-Tech_Risk - מסמכים\Clients\2025\Deel\DA\Deel IT Audit Q4-25\01 - Org files\Payout data Q4 2025\Payment Table contractor withdrawal.csv',
    FORMAT = 'CSV',
    FIRSTROW = 2
) AS t;

