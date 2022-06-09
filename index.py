from b3 import (
    get_initials,
    get_banks_report, 
    get_dre_report,
    transform_to_dataframe,
    send_to_google_sheets,
    toast
)
import constants

banks = get_banks_report()[0]
# SFSA, BICB

print('LIST OF BANKS')
for bank in banks:
    print(bank[0], '->', bank[1])

for bank in banks:

    for flow in constants.REPORT_FLOWS:
        df = transform_to_dataframe(
            get_dre_report(bank[0], flow), 
            constants.DRE_REPORT_CATEGORICAL_COLUMNS,
            bank[1]
        )
        print(df)
        short_name = get_initials(flow)
        if df is not None:
            send_to_google_sheets(bank[0], df, short_name)
            toast('Send Google Sheets', f'{bank[1]} - {short_name} atualizados com sucesso!')