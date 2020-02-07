from datetime import datetime


def json_to_edifact(payload: dict):
    now = datetime.now()
    time_stamp = "{:04d}{:02d}{:02d}{:02d}{:02d}".format(
        now.year, now.month, now.day, now.hour, now.minute
    )
    edifact_file = "1\\fileHeader\\SPIRE\CHIEF\\licenceData\\{}\\{}".format(
        time_stamp, 1234
    )

    i = 1
    for licence_payload in payload.get("licences"):
        i += 1
        licence = licence_payload.get("licence")
        edifact_file += "\n{}\\licence\\{}\\{}\\{}\\{}\\{}\\{}\\{}".format(
            i,
            34567,
            licence.get("action"),
            licence.get("licence_reference"),
            licence.get("licence_type"),
            licence.get("usage"),
            licence.get("start_date"),
            licence.get("end_date"),
        )
        for trader in licence_payload.get("traders"):
            i += 1
            edifact_file += "\n{}\\trader\\{}\\{}\\{}\\{}\\{}\\{}\\{}\\{}\\{}\\{}\\{}".format(
                i,
                trader.get("turn"),
                trader.get("rpa_trader_id"),
                trader.get("start_date"),
                trader.get("end_date"),
                trader.get("name"),
                trader.get("address_1"),
                trader.get("address_2"),
                trader.get("address_3"),
                trader.get("address_4"),
                trader.get("address_5"),
                trader.get("postcode"),
            )
        if licence_payload.get("country_group"):
            i += 1
            edifact_file += "\n{}\\country\\\\{}\\{}".format(
                i, licence_payload.get("country_group"), licence_payload.get("use")
            )
        elif licence_payload.get("countries"):
            for country in licence_payload.get("countries"):
                i += 1
                edifact_file += "\n{}\\country\\{}\\\\{}".format(
                    i, country, licence_payload.get("use")
                )
        for trader in licence_payload.get("foreign_traders"):
            i += 1
            edifact_file += "\n{}\\foreignTrader\\{}\\{}\\{}\\{}\\{}\\{}\\{}".format(
                i,
                trader.get("name"),
                trader.get("address_1"),
                trader.get("address_2"),
                trader.get("address_3"),
                trader.get("address_4"),
                trader.get("address_5"),
                trader.get("postcode"),
            )
        i += 1
        edifact_file += "\n{}\\restrictions\\{}".format(
            i, licence_payload.get("restrictions")
        )
        g = 0
        for commodity in licence_payload.get("commodities"):
            i += 1
            edifact_file += "\n{}\\line"

    print("\n\n\n\n")
    print(edifact_file)
    return edifact_file
