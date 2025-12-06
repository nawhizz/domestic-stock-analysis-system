import FinanceDataReader as fdr
try:
    df = fdr.StockListing('KRX')
    print("Columns:", df.columns.tolist())
    if 'PBR' in df.columns:
        print("PBR found!")
    else:
        print("PBR NOT found.")
except Exception as e:
    print(e)
