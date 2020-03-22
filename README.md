# Memberbooth

A GUI application for letting members log in on a public machine and interact with their data. It connects to a [makeradmin](https://github.com/makerspace/makeradmin) backend where the data resides. Memberbooth can perform the following:
* Display current member status (lab membership end date)
* Print labels for storage boxes (with QR code that can be scanned with [box-terminator](https://github.com/makerspace/BoxTerminator-App)) and labels for other temporary storage.

Optional Slack usage logging can be enabled.

## Prerequisites

* You need to obtain a token from the makeradmin backend that has the correct permissions for accessing the "memberbooth" endpoints.
* Python 3.7

## Installation

Install the required Python 3.7 packages and download Bebas-Neue font:

```bash
make init
```

## Usage

### Starting up the memberbooth
*memberbooth.py* runs the memberbooth GUI application.

```bash
./memberbooth.py
```

If you want to run against a custom backend (e.g. for development purposes), then you need to supply the `-u` argument.

### Logging in
The memberbooth application is then logged in by running the *login.py* script. This script will log in to the backend and a optionally a slack notification system.

### Printing labels for members
*print_label.py* prints labels for members.

```bash
./print_label.py <member_number>
```
