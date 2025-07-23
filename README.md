# Censorship Circumvention Wizard

Simple proof-of-concept. The end goal is to create a tool that users in different countries and network environments can use to answer common questions:
1. Is my internet being censored or just not working normally?
2. If it's not working normally, what exactly is the issue?
3. If it's being censored, how can I circumvent it?

## Usage

:warning: **The default configuration is tailored for users in China. If you are in a different country you'll want to update the configuration parameters!**

You'll need `python3` installed on the device. To start the wizard, clone the repository, `cd` in and run: `python3 client.py`

The code for different tests is in the `tests/` directory. Each test is uniquely identified with a `testTag`. Individual test parameters are set in the `config.json` file, using the test's tag as the key:

```
{
  "testTag": {
    // test-specific parameters
  },
  ...
}
```

## Tests

### Route

Tests if the device has internet connectivity by trying to create a socket and connect it to a non-local address.

### DNS

Uses the system DNS resolver to try resolving allowed and blocked hostnames. Tests blocked hostnames for DNS cache poisoning.

### TCP

Tries to establish TCP connections to known allowed and blocked IP addresses.

### TLS

Tries to complete a TLS handshake with an IP address that is known to be allowed but subject to censorship (i.e. a "clean" foreign IP for users in China). Tests:
- Handshakes without any SNI
- SNIs known to be allowed
- SNIs known to be blocked

Also tests TLS record fragmentation as a circumvention method, by attempting a handshake to a blocked SNI but fragmenting the ClientHello.

## Make Your Own Test

If you want to write your own custom test, just implement the interface described in `testInterface.py`, save the test module in the `tests/` directory, and add the test parameters to `config.json`.
