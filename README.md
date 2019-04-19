# Memberbooth

A GUI application for letting members log in on a public machine and interact with their data. It connects to a [makeradmin](https://github.com/makerspace/makeradmin) backend where the data resides. Memberbooth can perform the following:
* Display current member status (lab membership end date)
* Print storage box labels that has a QR code

## Prerequisites

* You need to obtain a token from the makeradmin backend that has the correct permissions for accessing the "memberbooth" endpoints.
* Python 3.7

## Installation

Install the Python 3.7 packages that are needed:

```bash
pip install -r requirements
```

## Usage

### Starting up the memberbooth
*memberbooth.py* runs the memberbooth GUI application.

```bash
./memberbooth.py $makeradmin_token
```

If you want to run against a custom backend (e.g. for development purposes), then you need to supply the `-u` argument.

### Printing labels for members
*print_label.py* prints labels for members.

```bash
./print_label.py $makeradmin_token $member_number
```
