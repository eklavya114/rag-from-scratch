"""
compliance_notes.py

This file is written for reading, nothing here needs to run. It briefly
explains a few GDPR-style compliance concepts in plain words, as
background for why this project's data_retention.py, access_control.py,
and pii_redaction.py were built the way they were. This is NOT legal
advice, and no part of this file should be treated as a legal
conclusion.
"""

GDPR_STYLE_RIGHTS = """
GDPR-STYLE RIGHTS, IN PLAIN WORDS

Several privacy regulations around the world (GDPR in the EU being the
most well known, with similar laws elsewhere) give individuals certain
rights over data collected about them. Three of the most common:

- RIGHT OF ACCESS: a person can ask "what data do you have about me,"
  and the service has to actually be able to answer that, which means
  data about a specific person has to be findable in the first place,
  not scattered across systems with no way to search it by person.

- RIGHT TO DELETION (sometimes called "the right to be forgotten"): a
  person can ask for their data to be deleted, and the service has to
  actually be able to delete it, not just stop showing it in a user
  interface while it quietly remains in a database or a backup
  somewhere. data_retention.py's delete_all_for_user() is a small,
  direct illustration of what this requires: a real, callable way to
  remove every record tied to one specific person, on demand.

- DATA MINIMIZATION: collect and keep only the data actually needed for
  a stated purpose, and only for as long as that purpose requires. This
  is why data_retention.py applies a retention period at all, and why
  pii_redaction.py and safe_logging_v2.py exist: collecting an email
  address is sometimes necessary, logging it in full, forever, in every
  debug log line, usually is not.
"""

DATA_PROCESSING_RECORDS_AND_DPIAS = """
DATA PROCESSING RECORDS AND DPIAS, IN PLAIN WORDS

A DATA PROCESSING RECORD is a written description of what personal data
a system collects, why, where it is stored, who can access it, and how
long it is kept. Many regulations require an organization to actually
maintain one of these for systems that handle personal data, not just
to generally behave responsibly, but to have a specific, reviewable
written account of what happens to that data.

A DPIA (Data Protection Impact Assessment) is a more formal written
review, usually required before launching a system that poses a higher
privacy risk (processing a lot of personal data, or sensitive categories
of it). It asks, in writing, before launch: what personal data will this
system touch, what could go wrong, and what has been done to reduce that
risk. Think of it as the privacy equivalent of a security review before
a risky deployment, a deliberate pause to write down the risks BEFORE
they become real incidents, not after.

Today's experiment (and this entire project) is small enough, and
synthetic enough, that neither a formal processing record nor a DPIA was
actually needed to build it. A real service handling real user data
would need both.
"""

NOT_LEGAL_ADVICE = """
THIS IS NOT LEGAL ADVICE

Nothing in this file, or anywhere else in this project, constitutes
legal advice. Which regulations actually apply to a real system depends
on where its users are located, what kind of data it processes, what
industry it operates in, and details a general explanation like this one
cannot account for. Before launching any real system that touches real
personal data, get an actual lawyer, with expertise in privacy and data
protection law, to review it. This project is a teaching exercise built
entirely on synthetic data and a toy service; treat every explanation
above as a starting point for understanding the IDEAS, not as a
compliance checklist to rely on.
"""


def main():
    print("=== Compliance Notes (reading material, nothing here runs) ===\n")
    print(GDPR_STYLE_RIGHTS)
    print(DATA_PROCESSING_RECORDS_AND_DPIAS)
    print(NOT_LEGAL_ADVICE)


if __name__ == "__main__":
    main()
