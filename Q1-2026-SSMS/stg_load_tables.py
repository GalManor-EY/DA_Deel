
SELECT *
INTO stg_payout_q4_2025
FROM OPENROWSET(
    BULK 'C:\data\payout_q4_2025.csv',
    FORMAT = 'CSV',
    FIRSTROW = 2
) AS t;



