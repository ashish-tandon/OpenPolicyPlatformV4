from utils import CSVScraper


class CambridgePersonScraper(CSVScraper):
    organization_classification = "legislature"
    # http://geohub.cambridge.ca/datasets/elected-officials
    csv_url = "https://maps.cambridge.ca/Images/OpenData/SharedDocuments/ElectedOfficials.csv"
