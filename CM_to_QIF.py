# !/usr/bin/python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass

import bs4.element
from bs4 import BeautifulSoup
from typing import List


@dataclass
class Transaction:
    symbol: str
    int_part: str
    decimal_part: str
    payment_info: str
    transaction_label: str
    date: str


def parse_transaction_tr(tr: bs4.element.Tag) -> Transaction:
    tds = tr.find_all("td", recursive=False)

    transaction_date = tds[0].text

    further_infos_container = tds[1].find_all("div", recursive=False)[-1].div
    further_infos = further_infos_container.find_all("div")  # type: list[bs4.element.Tag]
    payment_info = list(further_infos[0].stripped_strings)[-1]
    transaction_label = list(further_infos[1].stripped_strings)[0]
    if "Date de valeur" in transaction_label:
        transaction_label = None

    raw_amount = tds[2].text.replace(" ", "").replace(" ", "").replace("EUR", "")
    symbol = raw_amount[0]
    int_part = raw_amount[1:].split(",")[0]
    decimal_part = raw_amount[1:].split(",")[1]

    return Transaction(
        symbol=symbol, int_part=int_part, decimal_part=decimal_part,
        payment_info=payment_info, transaction_label=transaction_label,
        date=transaction_date
    )


def find_transactions_tbody(soup: bs4.element.Tag) -> bs4.element.Tag:
    tables = soup.find(id="ei_tpl_content").find_all("table")
    for table in tables:
        tbodies = table.find_all("tbody")
        for (i, tbody) in enumerate(tbodies):
            if "Opérations enregistrées" in tbody.text:
                return tbodies[i+1]


def write_transactions_as_QIF(out_file_path: str, transactions: List[Transaction]):
    with open(out_file_path, "w") as file:
        file.write("!Type:Bank\n")
        for t in transactions:
            qif_transaction = f"D{t.date}\n"
            qif_transaction += f"T{t.symbol}{t.int_part}.{t.decimal_part}\n"
            if t.transaction_label is not None:
                qif_transaction += f"P{t.transaction_label} {t.payment_info}\n"
            else:
                qif_transaction += f"P{t.payment_info}\n"
            qif_transaction += "^\n"
            file.write(qif_transaction)


def main():
    transactions = []  # type: list[Transaction]

    with open("input.html") as html_file:
        soup = BeautifulSoup(html_file, "html.parser")
        transaction_tbody = find_transactions_tbody(soup=soup)
        transaction_trs = transaction_tbody.find_all("tr")
        for (i, transaction_tr) in enumerate(transaction_trs):
            try:
                transaction = parse_transaction_tr(tr=transaction_tr)
            except Exception as e:
                print(transaction_tr)
                raise e

            print(i, ": ", transaction.transaction_label, transaction.payment_info)
            transactions.append(transaction)
        print(f"Found {len(transactions)} transactions")

    write_transactions_as_QIF(out_file_path="out.qif", transactions=transactions)


if __name__ == "__main__":
    main()
